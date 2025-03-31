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
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.login.auth import Auth
from antarest.study.model import NonStudyFolderDTO, WorkspaceMetadata
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
    bp = APIRouter(prefix="/v1/private")
    auth = Auth(config)

    @bp.get(
        "/explorer/{workspace}/_list_dir",
        summary="For a given directory, list sub directories that aren't studies",
        response_model=List[NonStudyFolderDTO],
    )
    def list_dir(
        workspace: str,
        path: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[NonStudyFolderDTO]:
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

    @bp.post(
        "/explorer/external/_open",
        summary="For a given study path, import the study",
        response_model=str,
    )
    def open_external_study(path: Path, current_user: JWTUser = Depends(auth.get_current_user)) -> str:
        """
        This endpoint create a raw study in DB for the study at the given path.
        Args:
            path: The file system path to the external study.
            current_user: user that perform the request.
        Returns:
            str: The unique identifier of the opened study.
        """

        logger.info(f"Open study under path {path}")
        params = RequestParameters(user=current_user)
        study_id = explorer.open_external_study(path, params)
        return study_id

    @bp.delete(
        "/explorer/external/_close/{uuid}",
        summary="For a given UUID, close the external study",
        response_model=str,
    )
    def close_external_study(uuid: str, current_user: JWTUser = Depends(auth.get_current_user)) -> str:
        """
        This endpoint delete a raw study from DB.
        Args:
            uuid: id of the study to delete.
            current_user: user that perform the request.
        Returns:
            str: empty string.
        """
        logger.info(f"Deleting study {uuid}")
        params = RequestParameters(user=current_user)
        explorer.close_external_study(uuid, params)
        return ""

    @bp.get(
        "/explorer/_list_workspaces",
        summary="List all workspaces",
        response_model=List[WorkspaceMetadata],
    )
    def list_workspaces(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[WorkspaceMetadata]:
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
