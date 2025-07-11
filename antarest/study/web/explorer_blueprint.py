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
from typing import List

from fastapi import APIRouter

from antarest.core.config import Config
from antarest.login.auth import Auth
from antarest.study.model import FolderDTO, WorkspaceDTO
from antarest.study.storage.explorer_service import Explorer

logger = logging.getLogger(__name__)


def create_explorer_routes(config: Config, explorer: Explorer) -> APIRouter:
    """
    Endpoint implementation for explorer management
    Args:
        explorer: explorer service facade to handle request
        config: main server configuration

    Returns:

    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1/private", dependencies=[auth.required()])

    @bp.get(
        "/explorer/{workspace}/_list_dir",
        summary="For a given directory, list sub directories.",
        response_model=List[FolderDTO],
    )
    def list_dir(workspace: str, path: str) -> List[FolderDTO]:
        """
        Endpoint to list sub directories of a given directory
        Args:
            path: path to the directory to scan
            current_user: user that perform the request

        Returns:
            List of sub directories

        """
        logger.info(f"Listing directory {path} in workspace {workspace}")
        return explorer.list_dir(workspace, path)

    @bp.get(
        "/explorer/_list_workspaces",
        summary="List all workspaces",
        response_model=List[WorkspaceDTO],
    )
    def list_workspaces() -> List[WorkspaceDTO]:
        """
        Endpoint to list workspaces
        Args:
            current_user: user that perform the request

        Returns:
            List of workspace

        """
        logger.info("Listing workspaces")
        return explorer.list_workspaces()

    return bp
