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
Utility to set up a dishka container on a FastAPI app for unit tests.
Replaces the old pattern of creating AppState and setting app.state.app_state.
"""

from typing import Any
from unittest.mock import Mock

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.tasks.service import ITaskService
from antarest.eventbus.connections import ConnectionManager
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.service import LauncherService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.output.output_service import OutputService
from antarest.study.directory_service import DirectoryService
from antarest.study.service import StudyService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher


class MockServicesProvider(Provider):
    """
    Provides mock services for unit tests.
    Accepts a Config and an optional services mock (duck-typed).
    """

    scope = Scope.APP

    def __init__(self, config: Config, services: Any = None) -> None:
        super().__init__()
        self._config = config
        self._services = services

    @provide
    def config(self) -> Config:
        return self._config

    @provide
    def connection_manager(self) -> ConnectionManager:
        return Mock(spec=ConnectionManager)

    @provide
    def study_service(self) -> StudyService:
        return self._services.study if self._services else Mock(spec=StudyService)

    @provide
    def directory_service(self) -> DirectoryService:
        return self._services.directory if self._services else Mock(spec=DirectoryService)

    @provide
    def login_service(self) -> LoginService:
        return self._services.user if self._services else Mock(spec=LoginService)

    @provide
    def launcher_service(self) -> LauncherService:
        launcher = self._services.launcher if self._services else Mock(spec=LauncherService)
        if launcher is None:
            raise ValueError("Launcher service is not configured.")
        return launcher

    @provide
    def matrix_service(self) -> MatrixService:
        return self._services.matrix if self._services else Mock(spec=MatrixService)

    @provide
    def file_transfer_manager(self) -> FileTransferManager:
        return self._services.file_transfer_manager if self._services else Mock(spec=FileTransferManager)

    @provide
    def output_service(self) -> OutputService:
        return self._services.output_service if self._services else Mock(spec=OutputService)

    @provide
    def favorite_study_service(self) -> FavoriteStudyService:
        return self._services.favorite_study if self._services else Mock(spec=FavoriteStudyService)

    @provide
    def favorite_directory_service(self) -> FavoriteDirectoryService:
        return self._services.favorite_directory if self._services else Mock(spec=FavoriteDirectoryService)

    @provide
    def task_service(self) -> ITaskService:
        return self._services.task_service if self._services else Mock(spec=ITaskService)

    @provide
    def maintenance_service(self) -> MaintenanceService:
        return self._services.maintenance if self._services else Mock(spec=MaintenanceService)

    @provide
    def watcher(self) -> Watcher:
        return self._services.watcher if self._services else Mock(spec=Watcher)

    @provide
    def explorer(self) -> Explorer:
        return self._services.explorer if self._services else Mock(spec=Explorer)

    @provide
    def event_bus(self) -> IEventBus:
        return self._services.event_bus if self._services else Mock(spec=IEventBus)

    @provide
    def cache(self) -> ICache:
        return self._services.cache if self._services else Mock(spec=ICache)


def setup_test_dishka(app: FastAPI, config: Config, services: Any = None) -> None:
    """
    Set up a dishka container on a FastAPI app for unit tests.

    Replaces the old pattern:
        app.state.app_state = AppState(config=config, services=services, ws_manager=Mock())

    Usage:
        setup_test_dishka(app, config)               # all mocks
        setup_test_dishka(app, config, services)      # real services (duck-typed mock)
    """
    container = make_async_container(MockServicesProvider(config, services))
    setup_dishka(container, app)
    app.state.config = config
