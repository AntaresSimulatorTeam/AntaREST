# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from http import HTTPStatus
from http.client import HTTPException
from typing import Any, List

from fastapi import APIRouter, Depends
from pydantic import DirectoryPath

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import NonStudyFolder
from antarest.study.storage.explorer_service import Explorer

logger = logging.getLogger(__name__)


class BadPathFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


def create_explorer_routes(config: Config, explorer: Explorer) -> APIRouter:
    """
    Endpoint implementation for explorer management
    Args:
        explorer: explorer service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/explorer/{workspace}/_list_dir",
        summary="Launch list sub dir in selected directory",
        response_model=List[NonStudyFolder],
    )
    def list_dir(
        workspace: str,
        path: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[NonStudyFolder]:
        """
        Endpoint to list sub directories of a given directory
        Args:
            path: path to the directory to scan
            current_user: user that perform the request

        Returns:
            List of sub directories

        """

        l = explorer.list_dir(workspace, path)
        return l

    @bp.get(
        "/explorer/_list_workspaces",
        summary="Launch list sub dir in selected directory",
        response_model=List[str],
    )
    def list_workspaces(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[str]:
        """
        Endpoint to list workspaces
        Args:
            current_user: user that perform the request

        Returns:
            List of workspace

        """
        l = explorer.list_workspaces()
        return l

    return bp
