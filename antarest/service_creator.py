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
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, TypeVar

import redis
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.pool import NullPool
from starlette.requests import Request
from starlette.responses import JSONResponse

from antarest.blobstore.blob_garbage_collector import BlobGarbageCollector
from antarest.blobstore.main import build_blob_service
from antarest.blobstore.service import BlobService
from antarest.core.application import AppBuildContext
from antarest.core.cache.main import build_cache
from antarest.core.config import Config, RedisConfig
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.filetransfer.main import build_filetransfer_service
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.filetransfer.web import create_file_transfer_api
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.main import build_maintenance_manager
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.maintenance.web import create_maintenance_api
from antarest.core.metrics import add_db_metrics
from antarest.core.persistence import upgrade_db
from antarest.core.tasks.main import build_taskjob_manager
from antarest.core.tasks.service import TaskJobService
from antarest.core.tasks.web import create_tasks_api
from antarest.core.typing import Supplier
from antarest.eventbus.main import build_eventbus
from antarest.eventbus.web import ConnectionManager
from antarest.fastapi_jwt_auth.exceptions import AuthJWTException
from antarest.launcher.main import build_launcher
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.login.main import build_login
from antarest.login.service import LoginService
from antarest.login.web import create_login_api, create_user_api
from antarest.matrixstore.main import build_matrix_service
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.matrixstore.service import MatrixService
from antarest.study.directory_service import DirectoryService
from antarest.study.main import build_study_service
from antarest.study.repository import DirectoryRepository
from antarest.study.service import StudyService
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.output_service import OutputService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.web.directory_blueprint import create_directory_routes
from antarest.study.web.explorer_blueprint import create_explorer_routes
from antarest.study.web.output_blueprint import create_output_routes
from antarest.study.web.raw_studies_blueprint import create_raw_study_routes
from antarest.study.web.studies_blueprint import create_study_routes
from antarest.study.web.study_data_blueprint import create_study_data_routes
from antarest.study.web.variant_blueprint import create_study_variant_routes
from antarest.study.web.watcher_blueprint import create_watcher_routes
from antarest.study.web.xpansion_studies_blueprint import create_xpansion_routes
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
    BLOB_GC = "blob_gc"


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

    extra: dict[str, Any] = {}
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

    add_db_metrics(config)

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


# TODO: connection manager optional
def create_event_bus(connection_manager: ConnectionManager, config: Config) -> Tuple[IEventBus, Optional[redis.Redis]]:
    redis_client = new_redis_instance(config.redis) if config.redis is not None else None
    return (
        build_eventbus(connection_manager, True, redis_client),
        redis_client,
    )


@dataclass(frozen=True)
class CoreServices:
    cache: ICache
    event_bus: IEventBus
    task_service: TaskJobService
    file_transfer_manager: FileTransferManager
    login_service: LoginService
    matrix_service: MatrixService
    study_service: StudyService
    output_service: OutputService
    blob_service: BlobService
    directory_service: DirectoryService
    connection_manager: ConnectionManager


def create_core_services(config: Config) -> CoreServices:
    connection_manager = ConnectionManager()
    event_bus, redis_client = create_event_bus(connection_manager, config)
    cache = build_cache(config=config, redis_client=redis_client)
    task_service = build_taskjob_manager(config, event_bus)
    filetransfer_service = build_filetransfer_service(event_bus, config)
    login_service = build_login(config, event_bus=event_bus)
    matrix_service = build_matrix_service(
        config=config,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        service=None,
    )
    blob_service = build_blob_service(config=config, service=None)

    directory_repository = DirectoryRepository()
    directory_service = DirectoryService(
        directory_repository=directory_repository,
    )

    study_service, output_service = build_study_service(
        config,
        matrix_service=matrix_service,
        cache=cache,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        event_bus=event_bus,
        blob_service=blob_service,
        directory_service=directory_service,
    )
    return CoreServices(
        cache=cache,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=filetransfer_service,
        login_service=login_service,
        matrix_service=matrix_service,
        study_service=study_service,
        output_service=output_service,
        blob_service=blob_service,
        directory_service=directory_service,
        connection_manager=connection_manager,
    )


def create_matrix_gc(config: Config, matrix_service: MatrixService) -> MatrixGarbageCollector:
    return MatrixGarbageCollector(
        matrix_service=matrix_service,
        sleeping_time=config.storage.matrix_gc_sleeping_time,
        dry_run=config.storage.matrix_gc_dry_run,
        retention_time=config.storage.matrix_gc_retention_time,
    )


def create_blob_gc(config: Config, blob_service: BlobService) -> BlobGarbageCollector:
    return BlobGarbageCollector(
        blob_service=blob_service,
        sleeping_time=config.storage.blob_gc_sleeping_time,
        dry_run=config.storage.blob_gc_dry_run,
    )


def create_watcher(
    config: Config,
    study_service: Optional[StudyService] = None,
) -> Watcher:
    if study_service:
        watcher = Watcher(
            config=config,
            study_service=study_service,
            task_service=study_service.task_service,
        )
    else:
        core_services = create_core_services(config)
        watcher = Watcher(
            config=config,
            study_service=core_services.study_service,
            task_service=core_services.task_service,
        )
    return watcher


def create_explorer(config: Config) -> Explorer:
    return Explorer(config=config)


def create_archive_worker(
    config: Config,
    workspace: str,
    event_bus: IEventBus,
    local_root: Path = Path("/"),
) -> AbstractWorker:
    return ArchiveWorker(event_bus, workspace, local_root, config)


@dataclass(frozen=True)
class Services:
    watcher: Watcher
    explorer: Explorer
    event_bus: IEventBus
    study: StudyService
    output: OutputService
    matrix: MatrixService
    user: LoginService
    cache: ICache
    maintenance: MaintenanceService
    task: TaskJobService
    directory: DirectoryService
    ftm: FileTransferManager
    launcher: Optional[LauncherService] = None
    matrix_gc: Optional[MatrixGarbageCollector] = None
    auto_archiver: Optional[AutoArchiveService] = None
    blob_gc: Optional[BlobGarbageCollector] = None


def create_services(config: Config, create_all: bool = False) -> Services:
    core_services = create_core_services(config)

    maintenance_service = build_maintenance_manager(
        config=config, cache=core_services.cache, event_bus=core_services.event_bus
    )

    launcher = build_launcher(
        config,
        study_service=core_services.study_service,
        output_service=core_services.output_service,
        login_service=core_services.login_service,
        event_bus=core_services.event_bus,
        task_service=core_services.task_service,
        file_transfer_manager=core_services.file_transfer_manager,
        cache=core_services.cache,
    )

    watcher = create_watcher(config=config, study_service=core_services.study_service)
    explorer_service = create_explorer(config=config)

    matrix_garbage_collector = None
    if config.server.services and Module.MATRIX_GC.value in config.server.services or create_all:
        matrix_garbage_collector = create_matrix_gc(config, core_services.matrix_service)

    blob_garbage_collector = None
    if config.server.services and Module.BLOB_GC.value in config.server.services or create_all:
        blob_garbage_collector = create_blob_gc(config, core_services.blob_service)

    auto_archiver = None
    if config.server.services and Module.AUTO_ARCHIVER.value in config.server.services or create_all:
        auto_archiver = AutoArchiveService(core_services.study_service, core_services.output_service, config)

    # Important note:
    # those singleton services must be "started" ONLY when explictly asked.
    # Typically for a production multi-process deployment, they should not be started
    # for each HTTP worker, but only for one dedicated background worker.
    if watcher and Module.WATCHER in config.server.services:
        watcher.start()

    if matrix_garbage_collector and Module.MATRIX_GC in config.server.services:
        matrix_garbage_collector.start()
    if auto_archiver and Module.AUTO_ARCHIVER in config.server.services:
        auto_archiver.start()
    if blob_garbage_collector and Module.BLOB_GC in config.server.services:
        blob_garbage_collector.start()

    return Services(
        watcher=watcher,
        explorer=explorer_service,
        event_bus=core_services.event_bus,
        study=core_services.study_service,
        matrix=core_services.matrix_service,
        user=core_services.login_service,
        cache=core_services.cache,
        maintenance=maintenance_service,
        launcher=launcher,
        matrix_gc=matrix_garbage_collector,
        auto_archiver=auto_archiver,
        blob_gc=blob_garbage_collector,
        task=core_services.task_service,
        directory=core_services.directory_service,
        output=core_services.output_service,
        ftm=core_services.file_transfer_manager,
    )


T = TypeVar("T")


def _raises_if_none(supplier: Supplier[T | None]) -> Supplier[T]:
    def wrapped_supplier() -> T:
        value = supplier()
        if value is None:
            raise ValueError("Service not initialized")
        return value

    return wrapped_supplier


def create_routes(app_ctxt: AppBuildContext, services: Supplier[Services], config: Config) -> None:
    root = app_ctxt.api_root

    # Technical routes
    root.include_router(create_login_api(lambda: services().user))
    root.include_router(create_user_api(lambda: services().user, config))
    root.include_router(create_maintenance_api(lambda: services().maintenance, config))
    root.include_router(create_tasks_api(lambda: services().task, config))
    root.include_router(create_utils_routes(config))
    root.include_router(create_file_transfer_api(lambda: services().ftm, config))
    # TODO: filesystem

    @app_ctxt.app.exception_handler(AuthJWTException)
    def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> Any:
        return JSONResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            content={"detail": exc.message},
        )

    # Launcher
    root.include_router(create_launcher_api(_raises_if_none(lambda: services().launcher), config))

    # Studies
    root.include_router(create_study_routes(lambda: services().study, config))
    root.include_router(create_study_data_routes(lambda: services().study, config))
    root.include_router(create_xpansion_routes(lambda: services().study, config))
    root.include_router(create_raw_study_routes(lambda: services().study, config))
    root.include_router(create_study_variant_routes(lambda: services().study, config))

    root.include_router(create_explorer_routes(config, lambda: services().explorer))
    root.include_router(create_directory_routes(lambda: services().directory, config))
    root.include_router(create_watcher_routes(lambda: services().watcher, config))

    # Outputs
    root.include_router(create_output_routes(lambda: services().output, config))

    # TODO: Websockets
