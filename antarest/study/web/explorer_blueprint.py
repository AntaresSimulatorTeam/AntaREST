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
from typing import List

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from antarest.core.api_types import SanitizedStr
from antarest.core.utils.web import APITag
from antarest.dependencies import ExplorerDep, auth_required
from antarest.study.model import FolderDTO, WorkspaceDTO

logger = logging.getLogger(__name__)


def create_explorer_routes() -> APIRouter:
    """
    Endpoint implementation for explorer management
    """
    bp = APIRouter(
        prefix="/v1/private", tags=[APITag.explorer], dependencies=[Depends(auth_required)], route_class=DishkaRoute
    )

    @bp.get(
        "/explorer/{workspace}/_list_dir",
        summary="For a given directory, list sub directories.",
    )
    def list_dir(explorer: ExplorerDep, workspace: SanitizedStr, path: SanitizedStr) -> List[FolderDTO]:
        """
        Endpoint to list sub directories of a given directory
        Args:
            path: path to the directory to scan

        Returns:
            List of sub directories

        """
        logger.info(f"Listing directory {path} in workspace {workspace}")
        return explorer.list_dir(workspace, path)

    @bp.get(
        "/explorer/_list_workspaces",
        summary="List all workspaces",
    )
    def list_workspaces(explorer: ExplorerDep) -> List[WorkspaceDTO]:
        """
        Endpoint to list workspaces
        Args:

        Returns:
            List of workspace

        """
        logger.info("Listing workspaces")
        return explorer.list_workspaces()

    return bp
