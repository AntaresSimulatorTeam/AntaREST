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

from pathlib import Path
from typing import cast

from fastapi import BackgroundTasks
from starlette.requests import Request

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.tasks.service import ITaskService
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.service import LauncherService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.output.service import OutputService
from antarest.study.directory_service import DirectoryService
from antarest.study.service import StudyService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher


def get_config(request: Request) -> Config:
    return cast(Config, request.app.state.config)


def get_study_service(request: Request) -> StudyService:
    return cast(StudyService, request.app.state.study_service)


def get_directory_service(request: Request) -> DirectoryService:
    return cast(DirectoryService, request.app.state.directory_service)


def get_explorer(request: Request) -> Explorer:
    return cast(Explorer, request.app.state.explorer)


def get_watcher(request: Request) -> Watcher:
    return cast(Watcher, request.app.state.watcher)


def get_login_service(request: Request) -> LoginService:
    return cast(LoginService, request.app.state.login_service)


def get_launcher_service(request: Request) -> LauncherService:
    return cast(LauncherService, request.app.state.launcher_service)


def get_matrix_service(request: Request) -> MatrixService:
    return cast(MatrixService, request.app.state.matrix_service)


def get_file_transfer_manager(request: Request) -> FileTransferManager:
    return cast(FileTransferManager, request.app.state.file_transfer_manager)


def get_output_service(request: Request) -> OutputService:
    return cast(OutputService, request.app.state.output_service)


def get_favorite_study_service(request: Request) -> FavoriteStudyService:
    return cast(FavoriteStudyService, request.app.state.favorite_study_service)


def get_favorite_directory_service(request: Request) -> FavoriteDirectoryService:
    return cast(FavoriteDirectoryService, request.app.state.favorite_directory_service)


def get_task_service(request: Request) -> ITaskService:
    return cast(ITaskService, request.app.state.task_service)


def get_maintenance_service(request: Request) -> MaintenanceService:
    return cast(MaintenanceService, request.app.state.maintenance_service)


def get_tmp_export_file(request: Request, background_tasks: BackgroundTasks) -> Path:
    ftm: FileTransferManager = cast(FileTransferManager, request.app.state.file_transfer_manager)
    return ftm.request_tmp_file(background_tasks)
