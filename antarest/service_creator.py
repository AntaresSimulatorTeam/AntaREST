# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from pathlib import Path
from typing import Any

import redis
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.pool import NullPool

from antarest.blobstore.blob_garbage_collector import BlobGarbageCollector
from antarest.blobstore.main import build_blob_service
from antarest.blobstore.service import BlobService
from antarest.core.cache.main import build_cache
from antarest.core.config import Config, RedisConfig
from antarest.core.filetransfer.main import build_filetransfer_service
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.main import build_maintenance_manager
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.metrics import add_db_metrics
from antarest.core.persistence import upgrade_db
from antarest.core.remote.remote_executor import RemoteWorkerExecutor
from antarest.core.tasks.main import build_taskjob_manager
from antarest.core.tasks.service import ITaskService
from antarest.eventbus.main import build_eventbus
from antarest.favorite.repository import FavoriteDirectoryRepository, FavoriteStudyRepository
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.main import build_launcher
from antarest.launcher.service import LauncherService
from antarest.lfs.dir_lfs import DirLargeFileStorage
from antarest.login.main import build_login
from antarest.login.service import LoginService
from antarest.matrixstore.main import build_matrix_service
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.output.adapters import study_service_as_file_outputs_provider, study_service_as_studies_repository
from antarest.output.service import OutputService
from antarest.output.storage.file.repository import FileOutputRepository
from antarest.output.storage.file.storage import InStudyFileOutputStorage
from antarest.output.storage.output_storage import IOutputStorage, OutputStorageType
from antarest.output.storage.v2.repository import OutputV2Repository
from antarest.output.storage.v2.storage import V2OutputStorage
from antarest.output.variable_view.gc import VariableViewGarbageCollector
from antarest.study.adapters import adapt_output_service_to_study_service
from antarest.study.dao.database.database_blob_usage_provider import DatabaseBlobUsageProvider
from antarest.study.directory_service import DirectoryService
from antarest.study.main import build_study_service
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.tablemode.repository import TablemodeRepository
from antarest.tablemode.service import TableModeService
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.worker import AbstractWorker

logger = logging.getLogger(__name__)


SESSION_ARGS: dict[str, bool] = {
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
    VARIABLE_VIEW_GC = "variable_view_gc"


def init_db_engine(
    config: Config,
    auto_upgrade_db: bool,
    config_file: Path | None = None,
) -> Engine:
    if auto_upgrade_db:
        if not config_file:
            raise ValueError("config_file must be provided when auto_upgrade_db is True")
        upgrade_db(config_file)
    connect_args: dict[str, Any] = {}
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
        retry_on_error=[redis.ConnectionError, redis.TimeoutError],
    )
    return redis_client


def create_event_bus(config: Config) -> tuple[IEventBus, redis.Redis | None]:  # type: ignore
    redis_client = new_redis_instance(config.redis) if config.redis is not None else None
    return (
        build_eventbus(True, redis_client),
        redis_client,
    )


@dataclass
class CoreServices:
    cache: ICache
    event_bus: IEventBus
    task_service: ITaskService
    file_transfer_manager: FileTransferManager
    login_service: LoginService
    matrix_service: MatrixService
    study_service: StudyService
    directory_service: DirectoryService
    output_service: OutputService
    blob_service: BlobService
    favorite_study_service: FavoriteStudyService
    favorite_directory_service: FavoriteDirectoryService
    study_disk_space_repository: StudyDiskSpaceRepository
    tablemode_service: TableModeService


def build_favorite_service() -> tuple[FavoriteStudyService, FavoriteDirectoryService]:
    favorite_repository = FavoriteStudyRepository()
    favorite_study_service = FavoriteStudyService(favorite_study_repository=favorite_repository)

    favorite_directory_repository = FavoriteDirectoryRepository()
    favorite_directory_service = FavoriteDirectoryService(favorite_directory_repository=favorite_directory_repository)

    return favorite_study_service, favorite_directory_service


def build_tablemode_service() -> TableModeService:
    tablemode_repository = TablemodeRepository()
    return TableModeService(tablemode_repository=tablemode_repository)


def build_output_storage_list(config: Config, file_output_storage: InStudyFileOutputStorage) -> list[IOutputStorage]:
    output_v2_storage_config = config.storage.output.v2_output_storage
    if not output_v2_storage_config.enable:
        return [file_output_storage]
    tmp_dir = config.storage.tmp_dir / "outputs"
    lfs = DirLargeFileStorage(output_v2_storage_config.archive_dir)
    v2_storage = V2OutputStorage(
        tmp_dir=tmp_dir,
        archive_storage=lfs,
        repository=OutputV2Repository(),
        variables_dir=output_v2_storage_config.variables_dir,
    )

    if config.storage.output.default_storage_type == OutputStorageType.V2:
        # The first element of the list will be used when importing simulation results from the HPC
        return [v2_storage, file_output_storage]
    else:
        return [file_output_storage, v2_storage]


def build_output_service(
    study_service: StudyService,
    cache: ICache,
    task_service: ITaskService,
    filetransfer_service: FileTransferManager,
    event_bus: IEventBus,
    config: Config,
    matrix_service: ISimpleMatrixService,
) -> OutputService:
    remote_executor = RemoteWorkerExecutor(event_bus, config)
    file_output_storage = InStudyFileOutputStorage(
        outputs_provider=study_service_as_file_outputs_provider(study_service),
        cache=cache,
        remote_executor=remote_executor,
        repository=FileOutputRepository(),
    )

    storages = build_output_storage_list(config, file_output_storage)

    output_service = OutputService(
        studies_repository=study_service_as_studies_repository(study_service),
        storages=storages,
        task_service=task_service,
        file_transfer_manager=filetransfer_service,
        matrix_service=matrix_service,
        tmp_dir=config.storage.tmp_dir,
    )

    study_service.register_output_access(adapt_output_service_to_study_service(output_service))

    return output_service


def create_core_services(config: Config) -> CoreServices:
    event_bus, redis_client = create_event_bus(config)
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
    blob_service.register_usage_provider(DatabaseBlobUsageProvider())
    study_service, directory_service = build_study_service(
        config,
        matrix_service=matrix_service,
        cache=cache,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        event_bus=event_bus,
        blob_service=blob_service,
    )

    output_service = build_output_service(
        cache=cache,
        study_service=study_service,
        task_service=task_service,
        filetransfer_service=filetransfer_service,
        event_bus=event_bus,
        config=config,
        matrix_service=matrix_service,
    )

    favorite_study_service, favorite_directory_service = build_favorite_service()
    tablemode_service = build_tablemode_service()

    study_disk_space_repository = StudyDiskSpaceRepository()

    return CoreServices(
        cache=cache,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=filetransfer_service,
        login_service=login_service,
        matrix_service=matrix_service,
        study_service=study_service,
        directory_service=directory_service,
        output_service=output_service,
        blob_service=blob_service,
        favorite_study_service=favorite_study_service,
        favorite_directory_service=favorite_directory_service,
        tablemode_service=tablemode_service,
        study_disk_space_repository=study_disk_space_repository,
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
        lock_folder=config.storage.tmp_dir,
    )


def create_variable_view_gc(config: Config) -> VariableViewGarbageCollector:
    return VariableViewGarbageCollector(
        sleeping_time=config.storage.variable_view_gc_sleeping_time,
        dry_run=config.storage.variable_view_gc_dry_run,
        retention_time=config.storage.variable_view_gc_retention_days,
        lock_folder=config.storage.tmp_dir,
    )


def create_watcher(
    config: Config,
    study_service: StudyService | None = None,
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
    local_root: Path = Path("/"),
    event_bus: IEventBus | None = None,
) -> AbstractWorker:
    if not event_bus:
        event_bus, _ = create_event_bus(config)
    return ArchiveWorker(event_bus, workspace, local_root, config)


@dataclass(frozen=True)
class Services:
    watcher: Watcher
    explorer: Explorer
    event_bus: IEventBus
    study: StudyService
    directory: DirectoryService
    matrix: MatrixService
    favorite_study: FavoriteStudyService
    favorite_directory: FavoriteDirectoryService
    tablemode_service: TableModeService
    user: LoginService
    cache: ICache
    maintenance: MaintenanceService
    task_service: ITaskService
    file_transfer_manager: FileTransferManager
    output_service: OutputService
    launcher: LauncherService | None = None
    matrix_gc: MatrixGarbageCollector | None = None
    auto_archiver: AutoArchiveService | None = None
    blob_gc: BlobGarbageCollector | None = None
    variable_view_gc: VariableViewGarbageCollector | None = None


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

    variable_view_gc = None
    if config.server.services and Module.VARIABLE_VIEW_GC.value in config.server.services or create_all:
        variable_view_gc = create_variable_view_gc(config)

    return Services(
        watcher=watcher,
        explorer=explorer_service,
        event_bus=core_services.event_bus,
        study=core_services.study_service,
        directory=core_services.directory_service,
        matrix=core_services.matrix_service,
        favorite_study=core_services.favorite_study_service,
        favorite_directory=core_services.favorite_directory_service,
        tablemode_service=core_services.tablemode_service,
        user=core_services.login_service,
        cache=core_services.cache,
        maintenance=maintenance_service,
        task_service=core_services.task_service,
        file_transfer_manager=core_services.file_transfer_manager,
        output_service=core_services.output_service,
        launcher=launcher,
        matrix_gc=matrix_garbage_collector,
        auto_archiver=auto_archiver,
        blob_gc=blob_garbage_collector,
        variable_view_gc=variable_view_gc,
    )
