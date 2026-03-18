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

"""
Dishka dependency injection providers.

Each provider class groups related services and declares how to build them
via @provide methods. Dishka resolves the dependency graph automatically.
"""

import logging
from typing import Optional

import prometheus_client
import redis
from dishka import Provider, Scope, provide

from antarest.blobstore.repository import BlobContentRepository
from antarest.blobstore.service import BlobService
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.config import Config
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.metrics import TasksMetricsRecorder
from antarest.core.remote.remote_executor import RemoteWorkerExecutor
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import ITaskService, TaskJobService
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.connections import ConnectionManager, connect_event_bus
from antarest.eventbus.service import EventBusService
from antarest.favorite.repository import FavoriteDirectoryRepository, FavoriteStudyRepository
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.repository import JobResultRepository, SolverPresetsRepository
from antarest.launcher.service import LauncherService
from antarest.login.ldap import LdapService
from antarest.login.repository import (
    BotRepository,
    GroupRepository,
    IdentityRepository,
    RoleRepository,
    UserLdapRepository,
    UserRepository,
)
from antarest.login.service import LoginService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService
from antarest.output.adapters import study_service_as_file_outputs_provider, study_service_as_studies_repository
from antarest.output.output_service import OutputService
from antarest.output.storage.file_output_storage import InStudyFileOutputStorage
from antarest.output.storage.output_storage import IOutputStorage
from antarest.service_creator import new_redis_instance
from antarest.study.adapters import adapt_output_service_to_study_service
from antarest.study.dao.database.database_blob_usage_provider import DatabaseBlobUsageProvider
from antarest.study.directory_service import DirectoryService
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


class ConfigProvider(Provider):
    """Provides the application Config as a singleton."""

    scope = Scope.APP

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    @provide
    def config(self) -> Config:
        return self._config


class InfrastructureProvider(Provider):
    """Provides low-level infrastructure: event bus and cache."""

    scope = Scope.APP

    def __init__(self) -> None:
        super().__init__()
        self._redis_client: Optional[redis.Redis] = None  # type: ignore
        self._redis_initialized = False

    def _get_redis(self, config: Config) -> Optional[redis.Redis]:  # type: ignore
        if not self._redis_initialized:
            self._redis_client = new_redis_instance(config.redis) if config.redis is not None else None
            self._redis_initialized = True
        return self._redis_client

    @provide
    def event_bus(self, config: Config) -> IEventBus:
        redis_client = self._get_redis(config)
        return EventBusService(
            RedisEventBus(redis_client) if redis_client is not None else LocalEventBus(),
            autostart=True,
        )

    @provide
    def cache(self, config: Config) -> ICache:
        redis_client = self._get_redis(config)
        if redis_client is not None:
            cache: ICache = RedisCache(redis_client)
        else:
            cache = LocalCache(config=config.cache)
        logger.info("Redis cache" if config.redis is not None else "Local cache")
        cache.start()
        return cache


class CoreServicesProvider(Provider):
    """Provides all core business services."""

    scope = Scope.APP

    @provide
    def task_service(self, config: Config, event_bus: IEventBus) -> ITaskService:
        repository = TaskJobRepository()
        listeners = []
        if config.metrics.prometheus:
            listeners.append(TasksMetricsRecorder(prometheus_client.REGISTRY))
        return TaskJobService(config, repository, event_bus, listeners=listeners)

    @provide
    def file_transfer_manager(self, event_bus: IEventBus, config: Config) -> FileTransferManager:
        return FileTransferManager(repository=FileDownloadRepository(), event_bus=event_bus, config=config)

    @provide
    def login_service(self, config: Config, event_bus: IEventBus) -> LoginService:
        user_repo = UserRepository()
        identity_repo = IdentityRepository()
        bot_repo = BotRepository()
        group_repo = GroupRepository()
        role_repo = RoleRepository()
        ldap_repo = UserLdapRepository()
        ldap = LdapService(config=config, users=ldap_repo, groups=group_repo, roles=role_repo)
        return LoginService(
            user_repo=user_repo,
            identity_repo=identity_repo,
            bot_repo=bot_repo,
            group_repo=group_repo,
            role_repo=role_repo,
            ldap=ldap,
            event_bus=event_bus,
        )

    @provide
    def matrix_service(
        self,
        config: Config,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        login_service: LoginService,
    ) -> MatrixService:
        repo = MatrixRepository()
        content = MatrixContentRepository(config.storage.matrixstore, config.storage.matrixstore_format)
        dataset_repo = MatrixDataSetRepository()
        return MatrixService(
            repo=repo,
            repo_dataset=dataset_repo,
            matrix_content_repository=content,
            user_service=login_service,
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
            config=config,
        )

    @provide
    def blob_service(self, config: Config) -> BlobService:
        content = BlobContentRepository(config.storage.blobstore)
        service = BlobService(blob_content_repository=content)
        service.register_usage_provider(DatabaseBlobUsageProvider())
        return service

    @provide
    def directory_service(self) -> DirectoryService:
        return DirectoryService(directory_repository=DirectoryRepository())

    @provide
    def study_service(
        self,
        config: Config,
        login_service: LoginService,
        matrix_service: MatrixService,
        blob_service: BlobService,
        cache: ICache,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        event_bus: IEventBus,
        directory_service: DirectoryService,
    ) -> StudyService:
        mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
        study_factory = StudyFactory(matrix_mapper_factory=mapper_factory, cache=cache)
        metadata_repository = StudyMetadataRepository(cache)
        variant_repository = VariantStudyRepository(cache)
        job_result_repository = JobResultRepository()

        raw_study_service = RawStudyService(
            config=config, study_factory=study_factory, cache=cache, matrix_service=matrix_service
        )

        generator_matrix_constants = GeneratorMatrixConstants(matrix_service=matrix_service)
        generator_matrix_constants.init_constant_matrices()
        command_factory = CommandFactory(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=matrix_service,
            blob_service=blob_service,
        )
        variant_study_service = VariantStudyService(
            task_service=task_service,
            cache=cache,
            raw_study_service=raw_study_service,
            command_factory=command_factory,
            study_factory=study_factory,
            repository=variant_repository,
            event_bus=event_bus,
            config=config,
            matrix_service=matrix_service,
        )

        return StudyService(
            raw_study_service=raw_study_service,
            variant_study_service=variant_study_service,
            directory_service=directory_service,
            command_context=command_factory.command_context,
            user_service=login_service,
            repository=metadata_repository,
            job_result_repository=job_result_repository,
            event_bus=event_bus,
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
            cache_service=cache,
            config=config,
        )

    @provide
    def output_service(
        self,
        study_service: StudyService,
        cache: ICache,
        task_service: ITaskService,
        file_transfer_manager: FileTransferManager,
        event_bus: IEventBus,
        config: Config,
        matrix_service: MatrixService,
    ) -> OutputService:
        remote_executor = RemoteWorkerExecutor(event_bus, config)
        file_output_storage = InStudyFileOutputStorage(
            outputs_provider=study_service_as_file_outputs_provider(study_service),
            cache=cache,
            remote_executor=remote_executor,
        )
        storages: list[IOutputStorage] = [file_output_storage]
        output_service = OutputService(
            studies_repository=study_service_as_studies_repository(study_service),
            storages=storages,
            task_service=task_service,
            file_transfer_manager=file_transfer_manager,
            matrix_service=matrix_service,
            tmp_dir=config.storage.tmp_dir,
        )
        study_service.register_output_access(adapt_output_service_to_study_service(output_service))
        return output_service

    @provide
    def favorite_study_service(self) -> FavoriteStudyService:
        return FavoriteStudyService(favorite_study_repository=FavoriteStudyRepository())

    @provide
    def favorite_directory_service(self) -> FavoriteDirectoryService:
        return FavoriteDirectoryService(favorite_directory_repository=FavoriteDirectoryRepository())

    @provide
    def maintenance_service(self, config: Config, cache: ICache, event_bus: IEventBus) -> MaintenanceService:
        repository = MaintenanceRepository()
        return MaintenanceService(config, repository, event_bus, cache)

    @provide
    def launcher_service(
        self,
        config: Config,
        study_service: StudyService,
        output_service: OutputService,
        login_service: LoginService,
        event_bus: IEventBus,
        task_service: ITaskService,
        file_transfer_manager: FileTransferManager,
        cache: ICache,
    ) -> LauncherService:
        job_repository = JobResultRepository()
        solver_presets_repository = SolverPresetsRepository()
        return LauncherService(
            config=config,
            study_service=study_service,
            output_service=output_service,
            login_service=login_service,
            job_result_repository=job_repository,
            solver_presets_repository=solver_presets_repository,
            event_bus=event_bus,
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
            cache=cache,
        )


class BackgroundServicesProvider(Provider):
    """Provides background/lifecycle services."""

    scope = Scope.APP

    @provide
    def watcher(self, config: Config, study_service: StudyService, task_service: ITaskService) -> Watcher:
        return Watcher(config=config, study_service=study_service, task_service=task_service)

    @provide
    def explorer(self, config: Config) -> Explorer:
        return Explorer(config=config)

    @provide
    def connection_manager(self, event_bus: IEventBus) -> ConnectionManager:
        ws_manager = ConnectionManager()
        connect_event_bus(event_bus, ws_manager)
        return ws_manager
