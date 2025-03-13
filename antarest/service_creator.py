# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

import redis
from sqlalchemy import create_engine 
from sqlalchemy.engine.base import Engine 
from sqlalchemy.pool import NullPool 

from antarest.core.application import AppBuildContext
from antarest.core.cache.main import build_cache
from antarest.core.config import Config, RedisConfig
from antarest.core.filetransfer.main import build_filetransfer_service
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.main import build_maintenance_manager
from antarest.core.persistence import upgrade_db
from antarest.core.tasks.main import build_taskjob_manager
from antarest.core.tasks.service import ITaskService
from antarest.eventbus.main import build_eventbus
from antarest.launcher.main import build_launcher
from antarest.login.main import build_login
from antarest.login.service import LoginService
from antarest.matrixstore.main import build_matrix_service
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.service import StudyService
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.web.explorer_blueprint import create_explorer_routes
from antarest.study.web.watcher_blueprint import create_watcher_routes
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.worker import AbstractWorker

logger = logging.getLogger(__name__)


SESSION_ARGS: Mapping[str, bool] = {
    "autocommit": False,
    "expire_on_commit": False,
    "autoflush": False,
}
"""
This mapping can be used to instantiate a new session, for example:

>>> with sessionmaker(engine, **SESSION_ARGS)() as session:
...     session.execute("SELECT 1")
"""


class Module(StrEnum):
    APP = "app"
    WATCHER = "watcher"
    MATRIX_GC = "matrix_gc"
    ARCHIVE_WORKER = "archive_worker"
    AUTO_ARCHIVER = "auto_archiver"


def init_db_engine(
    config_file: Path,
    config: Config,
    auto_upgrade_db: bool,
) -> Engine:
    if auto_upgrade_db:
        upgrade_db(config_file)
    connect_args: Dict[str, Any] = {}
    if config.db.db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        connect_args["connect_timeout"] = config.db.db_connect_timeout

    extra = {}
    if config.db.pool_use_null:
        extra["poolclass"] = NullPool
    elif not config.db.db_url.startswith("sqlite"):
        if config.db.pool_pre_ping:
            extra["pool_pre_ping"] = True
        if config.db.pool_recycle:
            extra["pool_recycle"] = config.db.pool_recycle
        if config.db.pool_max_overflow:
            extra["max_overflow"] = config.db.pool_max_overflow
        if config.db.pool_size:
            extra["pool_size"] = config.db.pool_size
        if config.db.pool_use_lifo:
            extra["pool_use_lifo"] = config.db.pool_use_lifo

    engine = create_engine(config.db.db_url, echo=config.debug, connect_args=connect_args, **extra)

    return engine


def new_redis_instance(config: RedisConfig) -> redis.Redis:  # type: ignore
    redis_client = redis.Redis(
        host=config.host,
        port=config.port,
        password=config.password,
        db=0,
        retry_on_error=[redis.ConnectionError, redis.TimeoutError],  # type: ignore
    )
    return redis_client  # type: ignore


def create_event_bus(app_ctxt: Optional[AppBuildContext], config: Config) -> Tuple[IEventBus, Optional[redis.Redis]]:  # type: ignore
    redis_client = new_redis_instance(config.redis) if config.redis is not None else None
    return (
        build_eventbus(app_ctxt, config, True, redis_client),
        redis_client,
    )


def create_core_services(
    app_ctxt: Optional[AppBuildContext], config: Config
) -> Tuple[ICache, IEventBus, ITaskService, FileTransferManager, LoginService, MatrixService, StudyService]:
    event_bus, redis_client = create_event_bus(app_ctxt, config)
    cache = build_cache(config=config, redis_client=redis_client)
    filetransfer_service = build_filetransfer_service(app_ctxt, event_bus, config)
    task_service = build_taskjob_manager(app_ctxt, config, event_bus)
    login_service = build_login(app_ctxt, config, event_bus=event_bus)
    matrix_service = build_matrix_service(
        app_ctxt,
        config=config,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        service=None,
    )
    study_service = build_study_service(
        app_ctxt,
        config,
        matrix_service=matrix_service,
        cache=cache,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        event_bus=event_bus,
    )
    return (
        cache,
        event_bus,
        task_service,
        filetransfer_service,
        login_service,
        matrix_service,
        study_service,
    )


def create_watcher(
    config: Config,
    app_ctxt: Optional[AppBuildContext],
    study_service: Optional[StudyService] = None,
) -> Watcher:
    if study_service:
        watcher = Watcher(
            config=config,
            study_service=study_service,
            task_service=study_service.task_service,
        )
    else:
        _, _, task_service, _, _, _, study_service = create_core_services(app_ctxt, config)
        watcher = Watcher(
            config=config,
            study_service=study_service,
            task_service=task_service,
        )

    if app_ctxt:
        app_ctxt.api_root.include_router(create_watcher_routes(watcher=watcher, config=config))

    return watcher


def create_explorer(config: Config, app_ctxt: Optional[AppBuildContext]) -> Any:
    explorer = Explorer(config=config)
    if app_ctxt:
        app_ctxt.api_root.include_router(create_explorer_routes(config=config, explorer=explorer))

    return explorer


def create_matrix_gc(
    config: Config,
    app_ctxt: Optional[AppBuildContext],
    study_service: Optional[StudyService] = None,
    matrix_service: Optional[MatrixService] = None,
) -> MatrixGarbageCollector:
    if study_service and matrix_service:
        return MatrixGarbageCollector(
            config=config,
            study_service=study_service,
            matrix_service=matrix_service,
        )
    else:
        _, _, _, _, _, matrix_service, study_service = create_core_services(app_ctxt, config)
        return MatrixGarbageCollector(
            config=config,
            study_service=study_service,
            matrix_service=matrix_service,
        )


def create_archive_worker(
    config: Config,
    workspace: str,
    local_root: Path = Path("/"),
    event_bus: Optional[IEventBus] = None,
) -> AbstractWorker:
    if not event_bus:
        event_bus, _ = create_event_bus(None, config)
    return ArchiveWorker(event_bus, workspace, local_root, config)


def create_services(config: Config, app_ctxt: Optional[AppBuildContext], create_all: bool = False) -> Dict[str, Any]:
    services: Dict[str, Any] = {}

    (
        cache,
        event_bus,
        task_service,
        file_transfer_manager,
        user_service,
        matrix_service,
        study_service,
    ) = create_core_services(app_ctxt, config)

    maintenance_service = build_maintenance_manager(app_ctxt, config=config, cache=cache, event_bus=event_bus)

    launcher = build_launcher(
        app_ctxt,
        config,
        study_service=study_service,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=file_transfer_manager,
        cache=cache,
    )

    watcher = create_watcher(config=config, app_ctxt=app_ctxt, study_service=study_service)
    services["watcher"] = watcher

    explorer_service = create_explorer(config=config, app_ctxt=app_ctxt)
    services["explorer"] = explorer_service

    if config.server.services and Module.MATRIX_GC.value in config.server.services or create_all:
        matrix_garbage_collector = create_matrix_gc(
            config=config,
            app_ctxt=app_ctxt,
            study_service=study_service,
            matrix_service=matrix_service,
        )
        services["matrix_gc"] = matrix_garbage_collector

    if config.server.services and Module.AUTO_ARCHIVER.value in config.server.services or create_all:
        auto_archiver = AutoArchiveService(study_service, config)
        services["auto_archiver"] = auto_archiver

    services["event_bus"] = event_bus
    services["study"] = study_service
    services["launcher"] = launcher
    services["matrix"] = matrix_service
    services["user"] = user_service
    services["cache"] = cache
    services["maintenance"] = maintenance_service
    return services
