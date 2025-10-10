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

"""FastAPI routes for directory management."""

import logging
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Query

from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.login.utils import require_current_user
from antarest.study.directory_service import DirectoryService
from antarest.study.model import DirectoryCreateDTO, DirectoryDTO, DirectoryUpdateDTO, StudyMetadataDTO
from antarest.study.repository import AccessPermissions

logger = logging.getLogger(__name__)


def create_directory_routes(
    directory_service: DirectoryService,
    config: Config,
) -> APIRouter:
    """Create the directory routes for FastAPI."""
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

    @bp.get(
        "/directories",
        tags=[APITag.study_management],
        summary="List directories",
        response_model=List[DirectoryDTO],
    )
    def list_directories() -> List[DirectoryDTO]:
        """Get directories the current user has access to."""
        logger.info("Listing directories for current user")
        access_permissions = AccessPermissions.for_current_user()
        return directory_service.list_directories(access_permissions)

    @bp.get(
        "/directories/{directory_id}",
        tags=[APITag.study_management],
        summary="Get directory details",
        response_model=DirectoryDTO,
    )
    def get_directory(directory_id: str) -> DirectoryDTO:
        """Get directory details."""
        logger.info(f"Getting directory {directory_id}")
        access_permissions = AccessPermissions.for_current_user()
        return directory_service.get_directory(directory_id, access_permissions)

    @bp.get(
        "/directories/{directory_id}/studies",
        tags=[APITag.study_management],
        summary="List studies in directory",
        response_model=List[StudyMetadataDTO],
    )
    def list_studies_in_directory(directory_id: str) -> List[StudyMetadataDTO]:
        """Get all studies in a directory."""
        logger.info(f"Listing studies in directory {directory_id}")
        access_permissions = AccessPermissions.for_current_user()
        return directory_service.list_studies_in_directory(directory_id, access_permissions)

    @bp.post(
        "/directories",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Create a new directory",
        response_model=DirectoryDTO,
    )
    def create_directory(
        data: DirectoryCreateDTO,
        groups: str = Query("", description="Comma-separated list of group IDs to share with"),
    ) -> DirectoryDTO:
        """Create a new directory."""
        logger.info(f"Creating directory '{data.name}'")

        user = require_current_user()
        access_permissions = AccessPermissions.for_current_user()

        if groups:
            group_ids = [gid.strip() for gid in groups.split(",") if gid.strip()]
        else:
            group_ids = [group.id for group in user.groups]

        return directory_service.create_directory(data, user.id, group_ids, access_permissions)

    @bp.put(
        "/directories/{directory_id}",
        tags=[APITag.study_management],
        summary="Update directory",
        response_model=DirectoryDTO,
    )
    def update_directory(directory_id: str, data: DirectoryUpdateDTO) -> DirectoryDTO:
        """Update directory name or parent."""
        logger.info(f"Updating directory {directory_id}")
        access_permissions = AccessPermissions.for_current_user()
        return directory_service.update_directory(directory_id, data, access_permissions)

    @bp.delete(
        "/directories/{directory_id}",
        status_code=HTTPStatus.NO_CONTENT,
        tags=[APITag.study_management],
        summary="Delete directory",
    )
    def delete_directory(
        directory_id: str,
        cascade: bool = Query(
            False,
            description="If true, recursively delete all subdirectories and studies (DANGER: irreversible!)",
        ),
        force: bool = Query(
            False,
            description="If true, delete directory even if it contains studies (studies become orphaned)",
        ),
    ) -> None:
        """
        Delete a directory.
        - Default: only if empty
        - cascade=true: delete all subdirectories and studies (irreversible!)
        - force=true: orphan subdirectories and studies
        """
        logger.info(f"Deleting directory {directory_id} (cascade={cascade}, force={force})")
        access_permissions = AccessPermissions.for_current_user()
        directory_service.delete_directory(
            directory_id, cascade=cascade, force=force, access_permissions=access_permissions
        )

    return bp
