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

Service dependencies are provided by dishka via FromDishka annotations.
A few dependencies that need FastAPI-specific request context (auth, tmp files)
remain as FastAPI Depends().
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any, TypeAlias

from dishka.integrations.fastapi import FromDishka, inject
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
from antarest.eventbus.connections import ConnectionManager
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

# Type aliases for dishka-injected dependencies (used in endpoint signatures)

ConfigDep: TypeAlias = FromDishka[Config]
StudyServiceDep: TypeAlias = FromDishka[StudyService]
DirectoryServiceDep: TypeAlias = FromDishka[DirectoryService]
ExplorerDep: TypeAlias = FromDishka[Explorer]
WatcherDep: TypeAlias = FromDishka[Watcher]
LoginServiceDep: TypeAlias = FromDishka[LoginService]
LauncherServiceDep: TypeAlias = FromDishka[LauncherService]
MatrixServiceDep: TypeAlias = FromDishka[MatrixService]
FileTransferManagerDep: TypeAlias = FromDishka[FileTransferManager]
OutputServiceDep: TypeAlias = FromDishka[OutputService]
FavoriteStudyServiceDep: TypeAlias = FromDishka[FavoriteStudyService]
FavoriteDirectoryServiceDep: TypeAlias = FromDishka[FavoriteDirectoryService]
TaskServiceDep: TypeAlias = FromDishka[ITaskService]
MaintenanceServiceDep: TypeAlias = FromDishka[MaintenanceService]
ConnectionManagerDep: TypeAlias = FromDishka[ConnectionManager]


# Dependencies that still use FastAPI's Depends() because they need request context


@inject
def get_auth_service(
    request: HTTPConnection,
    response: Response,
    login_service: FromDishka[LoginService],
    config: FromDishka[Config],
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


AuthDep: TypeAlias = Annotated[AuthJWT, Depends(get_auth_service)]


@inject
def get_tmp_export_file(
    file_transfer_manager: FromDishka[FileTransferManager], background_tasks: BackgroundTasks
) -> Path:
    return file_transfer_manager.request_tmp_file(background_tasks)


TmpExportFileDep: TypeAlias = Annotated[Path, Depends(get_tmp_export_file)]


# Bridge dependency to get Config from dishka for use in auth_required.
# We don't use @inject on auth_required itself because it changes the async generator's
# execution context, which breaks contextvars (current_user_context).
@inject
def _get_config_from_dishka(config: FromDishka[Config]) -> Config:
    return config


_ConfigViaDishka: TypeAlias = Annotated[Config, Depends(_get_config_from_dishka)]


async def auth_required(
    auth_jwt: AuthDep,
    config: _ConfigViaDishka,
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
