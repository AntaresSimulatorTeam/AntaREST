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

Phase 1: wraps existing build_* functions and service_creator logic.
Phase 2 will inline the build logic directly into providers.
"""

from dishka import Provider, Scope, provide

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.tasks.service import ITaskService
from antarest.eventbus.connections import ConnectionManager, connect_event_bus
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.service import LauncherService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.output.output_service import OutputService
from antarest.service_creator import (
    Services,
    create_services,
)
from antarest.study.directory_service import DirectoryService
from antarest.study.service import StudyService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher


class ConfigProvider(Provider):
    """Provides the application Config as a singleton."""

    scope = Scope.APP

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    @provide
    def config(self) -> Config:
        return self._config


class ServicesProvider(Provider):
    """
    Phase 1 provider: wraps existing create_services() and exposes individual services.
    """

    scope = Scope.APP

    @provide
    def services(self, config: Config) -> Services:
        return create_services(config)

    @provide
    def event_bus(self, services: Services) -> IEventBus:
        return services.event_bus

    @provide
    def cache(self, services: Services) -> ICache:
        return services.cache

    @provide
    def task_service(self, services: Services) -> ITaskService:
        return services.task_service

    @provide
    def file_transfer_manager(self, services: Services) -> FileTransferManager:
        return services.file_transfer_manager

    @provide
    def login_service(self, services: Services) -> LoginService:
        return services.user

    @provide
    def matrix_service(self, services: Services) -> MatrixService:
        return services.matrix

    @provide
    def study_service(self, services: Services) -> StudyService:
        return services.study

    @provide
    def directory_service(self, services: Services) -> DirectoryService:
        return services.directory

    @provide
    def output_service(self, services: Services) -> OutputService:
        return services.output_service

    @provide
    def favorite_study_service(self, services: Services) -> FavoriteStudyService:
        return services.favorite_study

    @provide
    def favorite_directory_service(self, services: Services) -> FavoriteDirectoryService:
        return services.favorite_directory

    @provide
    def launcher_service(self, services: Services) -> LauncherService:
        launcher = services.launcher
        if launcher is None:
            raise ValueError("Launcher service is not configured.")
        return launcher

    @provide
    def maintenance_service(self, services: Services) -> MaintenanceService:
        return services.maintenance

    @provide
    def watcher(self, services: Services) -> Watcher:
        return services.watcher

    @provide
    def explorer(self, services: Services) -> Explorer:
        return services.explorer

    @provide
    def connection_manager(self, event_bus: IEventBus) -> ConnectionManager:
        ws_manager = ConnectionManager()
        connect_event_bus(event_bus, ws_manager)
        return ws_manager
