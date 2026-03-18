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
This module defines dependencies for all routes of the application.

TODO: should probably be less "centralized" ?
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any, TypeAlias, cast

from fastapi import BackgroundTasks, Depends
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.serde.json import from_json
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.eventbus.web import ConnectionManager
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.launcher.service import LauncherService
from antarest.login.auth import JwtSettings
from antarest.login.service import LoginService
from antarest.login.utils import current_user_context
from antarest.matrixstore.service import MatrixService
from antarest.output.output_service import OutputService
from antarest.study.directory_service import DirectoryService
from antarest.study.service import StudyService
from antarest.study.storage.explorer_service import Explorer
from antarest.study.storage.rawstudy.watcher import Watcher


def get_config(request: HTTPConnection) -> Config:
    return cast(Config, request.app.state.config)


def get_study_service(request: Request) -> StudyService:
    return cast(StudyService, request.app.state.study_service)


def get_directory_service(request: Request) -> DirectoryService:
    return cast(DirectoryService, request.app.state.directory_service)


def get_explorer(request: Request) -> Explorer:
    return cast(Explorer, request.app.state.explorer)


def get_watcher(request: Request) -> Watcher:
    return cast(Watcher, request.app.state.watcher)


def get_login_service(request: HTTPConnection) -> LoginService:
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


def get_auth_service(
    request: HTTPConnection,
    response: Response,
    login_service: LoginService = Depends(get_login_service),
    config: Config = Depends(get_config),
) -> AuthJWT:
    """
    Returns an AuthJWT instance which can be used for authenticating the request.

    Depends on config (in particular for disabling auth), and on login service to check for revoked tokens.
    """

    # TODO: that config part would better be done not on every request, not a blocker though
    if not config.security.disabled:

        @AuthJWT.load_config  # type: ignore
        def get_config() -> JwtSettings:
            return JwtSettings(
                authjwt_secret_key=config.security.jwt_key,
                authjwt_token_location=("headers", "cookies"),
                authjwt_cookie_csrf_protect=False,
            )

        # Set deny list (tokens which do not exist anymore in our DB)

        @AuthJWT.token_in_denylist_loader  # type: ignore
        def check_if_token_is_revoked(decrypted_token: Any) -> bool:
            subject = from_json(decrypted_token["sub"])
            user_id = subject["id"]
            token_type = subject["type"]
            with db():
                return token_type == "bots" and not login_service.exists_bot(user_id)

    match request:
        case Request():
            return AuthJWT(request, response)
        case WebSocket():
            return AuthJWT()
        case _:
            raise ValueError(f"Unsupported request type: {type(request)}")


def get_ws_manager(request: HTTPConnection) -> ConnectionManager:
    return cast(ConnectionManager, request.app.state.ws_manager)


# Type aliases to be used for injection in endpoints

AuthDep: TypeAlias = Annotated[AuthJWT, Depends(get_auth_service)]
ConfigDep: TypeAlias = Annotated[Config, Depends(get_config)]
StudyServiceDep: TypeAlias = Annotated[StudyService, Depends(get_study_service)]
DirectoryServiceDep: TypeAlias = Annotated[DirectoryService, Depends(get_directory_service)]
ExplorerDep: TypeAlias = Annotated[Explorer, Depends(get_explorer)]
WatcherDep: TypeAlias = Annotated[Watcher, Depends(get_watcher)]
LoginServiceDep: TypeAlias = Annotated[LoginService, Depends(get_login_service)]
LauncherServiceDep: TypeAlias = Annotated[LauncherService, Depends(get_launcher_service)]
MatrixServiceDep: TypeAlias = Annotated[MatrixService, Depends(get_matrix_service)]
FileTransferManagerDep: TypeAlias = Annotated[FileTransferManager, Depends(get_file_transfer_manager)]
OutputServiceDep: TypeAlias = Annotated[OutputService, Depends(get_output_service)]
FavoriteStudyServiceDep: TypeAlias = Annotated[FavoriteStudyService, Depends(get_favorite_study_service)]
FavoriteDirectoryServiceDep: TypeAlias = Annotated[FavoriteDirectoryService, Depends(get_favorite_directory_service)]
TaskServiceDep: TypeAlias = Annotated[ITaskService, Depends(get_task_service)]
MaintenanceServiceDep: TypeAlias = Annotated[MaintenanceService, Depends(get_maintenance_service)]
TmpExportFileDep: TypeAlias = Annotated[Path, Depends(get_tmp_export_file)]
ConnectionManagerDep: TypeAlias = Annotated[ConnectionManager, Depends(get_ws_manager)]


async def auth_required(
    auth_jwt: AuthDep,
    config: ConfigDep,
) -> AsyncGenerator[None, None]:
    """
    A FastAPI dependency to require authentication and set the current user context.

    Implementation note:
        This dependency MUST be async, otherwise it's executed in a thread which will
        generally not be the same as the one of the request.
    """
    if config.security.disabled:
        user = DEFAULT_ADMIN_USER
    else:
        auth_jwt.jwt_required()
        user = JWTUser.model_validate(from_json(auth_jwt.get_jwt_subject()))

    with current_user_context(user):
        yield
