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

"""
FastAPI routes for directory management.

This module provides REST API endpoints for managing directories in the managed workspace.
"""

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
    """
    Create the directory routes for FastAPI.

    Args:
        directory_service: The directory service instance.
        config: Application configuration.

    Returns:
        Configured APIRouter.
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

    @bp.get(
        "/directories",
        tags=[APITag.study_management],
        summary="List directories",
        response_model=List[DirectoryDTO],
    )
    def list_directories() -> List[DirectoryDTO]:
        """
        Get the list of directories the current user has access to.

        The user can see directories they own or directories shared with their groups.

        Returns:
            List of directory DTOs with full details.
        """
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
        """
        Get detailed information about a specific directory.

        Args:
            directory_id: The UUID of the directory.

        Returns:
            Directory DTO with full details.

        Raises:
            404: Directory not found.
            403: User doesn't have permission to access this directory.
        """
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
        """
        Get all studies contained in a specific directory.

        Args:
            directory_id: The UUID of the directory.

        Returns:
            List of studies in the directory.

        Raises:
            404: Directory not found.
            403: User doesn't have permission to access this directory.
        """
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
        """
        Create a new directory in the managed workspace.

        The directory will be owned by the current user and optionally shared with specified groups.

        Args:
            data: Directory creation data (name, parent_id).
            groups: Comma-separated group IDs for sharing (defaults to user's groups).

        Returns:
            Created directory DTO.

        Raises:
            404: Parent directory not found (if parent_id specified).
            403: User doesn't have permission to create in parent directory.
            409: Directory with same name already exists in this location.
        """
        logger.info(f"Creating directory '{data.name}'")

        user = require_current_user()
        access_permissions = AccessPermissions.for_current_user()

        # Parse group IDs
        if groups:
            group_ids = [gid.strip() for gid in groups.split(",") if gid.strip()]
        else:
            # Default to user's groups
            group_ids = [group.id for group in user.groups]

        return directory_service.create_directory(data, user.id, group_ids, access_permissions)

    @bp.put(
        "/directories/{directory_id}",
        tags=[APITag.study_management],
        summary="Update directory",
        response_model=DirectoryDTO,
    )
    def update_directory(directory_id: str, data: DirectoryUpdateDTO) -> DirectoryDTO:
        """
        Update a directory's name or parent location.

        Args:
            directory_id: The UUID of the directory to update.
            data: Update data (name, parent_id). Only provided fields will be updated.

        Returns:
            Updated directory DTO.

        Raises:
            404: Directory or new parent not found.
            403: User doesn't have permission to modify this directory.
            409: New name conflicts with existing directory in same location.
            400: Moving directory would create a cycle in the tree.
        """
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

        Three deletion modes:

        1. **Default** (cascade=false, force=false):
           - Only delete if directory is empty (no subdirectories, no studies)
           - Returns 409 Conflict if directory is not empty

        2. **Cascade** (cascade=true):
           - Recursively delete directory, all subdirectories, and all studies
           - ⚠️ **DANGER**: This is irreversible and will delete all studies!
           - User must have write permission on ALL contained studies

        3. **Force** (force=true):
           - Delete directory even if it contains studies
           - Studies become orphaned (directory_id set to NULL)
           - Studies remain accessible at root level

        Args:
            directory_id: The UUID of the directory to delete.
            cascade: Enable cascade deletion (delete all contents).
            force: Enable force deletion (orphan studies).

        Raises:
            404: Directory not found.
            403: User doesn't have permission to delete this directory.
            409: Directory not empty (when cascade=false and force=false).
        """
        logger.info(f"Deleting directory {directory_id} (cascade={cascade}, force={force})")
        access_permissions = AccessPermissions.for_current_user()
        directory_service.delete_directory(
            directory_id, cascade=cascade, force=force, access_permissions=access_permissions
        )

    return bp
