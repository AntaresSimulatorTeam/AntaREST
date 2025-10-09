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
Service layer for Directory management.

This module provides business logic for managing directories in the managed workspace.
"""

import logging
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, List, Sequence

from fastapi import HTTPException
from sqlalchemy import update

from antarest.core.model import PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.login.model import Group, GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Directory,
    DirectoryCreateDTO,
    DirectoryDTO,
    DirectoryUpdateDTO,
    OwnerInfo,
    StudyAdditionalData,
    StudyMetadataDTO,
)
from antarest.study.repository import AccessPermissions, DirectoryRepository, StudyFilter, StudyMetadataRepository

if TYPE_CHECKING:
    from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class DirectoryService:
    """
    Service for managing directories with business logic and permission checks.
    """

    def __init__(
        self,
        directory_repository: DirectoryRepository,
        study_repository: StudyMetadataRepository,
        study_service: "StudyService",
    ):
        """
        Initialize the service.

        Args:
            directory_repository: Repository for directory operations.
            study_repository: Repository for study operations (to check studies in directories).
            study_service: Study service for cascade deletions.
        """
        self.directory_repository = directory_repository
        self.study_repository = study_repository
        self.study_service = study_service

    def list_directories(self, access_permissions: AccessPermissions) -> List[DirectoryDTO]:
        """
        List all directories the user has access to.

        Args:
            access_permissions: User permissions for filtering.

        Returns:
            List of directory DTOs.
        """
        directories = self.directory_repository.get_all(access_permissions)
        return [self._to_dto(directory) for directory in directories]

    def get_directory(self, directory_id: str, access_permissions: AccessPermissions) -> DirectoryDTO:
        """
        Get a directory by ID with permission check.

        Args:
            directory_id: The directory ID.
            access_permissions: User permissions.

        Returns:
            Directory DTO.

        Raises:
            HTTPException: If directory not found or user has no permission.
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Directory '{directory_id}' not found")

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        return self._to_dto(directory)

    def create_directory(
        self,
        data: DirectoryCreateDTO,
        owner_id: int,
        group_ids: Sequence[str],
        access_permissions: AccessPermissions,
    ) -> DirectoryDTO:
        """
        Create a new directory.

        Args:
            data: Directory creation data.
            owner_id: Owner user ID.
            group_ids: List of group IDs to associate.
            access_permissions: User permissions (for parent access check).

        Returns:
            Created directory DTO.

        Raises:
            HTTPException: If validation fails or parent not found.
        """
        # Validate parent exists and user has access
        if data.parent_id:
            parent = self.directory_repository.get(data.parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=f"Parent directory '{data.parent_id}' not found"
                )

            if not self.directory_repository.has_permission(parent, access_permissions, write_access=True):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="You don't have permission to create directories in this parent",
                )

        # Check for duplicate name
        if self.directory_repository.has_duplicate_name(data.name, data.parent_id):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"A directory named '{data.name}' already exists in this location",
            )

        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Associate groups
        session = self.directory_repository.session
        directory.groups = [session.get(Group, gid) for gid in group_ids if session.get(Group, gid)]

        # Save
        saved_directory = self.directory_repository.save(directory)
        return self._to_dto(saved_directory)

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdateDTO,
        access_permissions: AccessPermissions,
    ) -> DirectoryDTO:
        """
        Update a directory.

        Args:
            directory_id: The directory ID to update.
            data: Update data.
            access_permissions: User permissions.

        Returns:
            Updated directory DTO.

        Raises:
            HTTPException: If directory not found, validation fails, or no permission.
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Directory '{directory_id}' not found")

        if not self.directory_repository.has_permission(directory, access_permissions, write_access=True):
            raise UserHasNotPermissionError()

        # Update name
        if data.name is not None:
            # Check for duplicate name (excluding current directory)
            if self.directory_repository.has_duplicate_name(data.name, directory.parent_id, exclude_id=directory_id):
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"A directory named '{data.name}' already exists in this location",
                )
            directory.name = data.name

        # Update parent
        if data.parent_id is not None:
            # Check for cycles
            if self.directory_repository.check_cycle(directory_id, data.parent_id):
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Cannot move directory: this would create a cycle in the directory tree",
                )

            # Validate new parent exists
            if data.parent_id != "":  # Empty string means move to root
                new_parent = self.directory_repository.get(data.parent_id)
                if new_parent is None:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND, detail=f"Parent directory '{data.parent_id}' not found"
                    )

                if not self.directory_repository.has_permission(new_parent, access_permissions, write_access=True):
                    raise HTTPException(
                        status_code=HTTPStatus.FORBIDDEN,
                        detail="You don't have permission to move directories to this parent",
                    )

            directory.parent_id = data.parent_id if data.parent_id != "" else None

        directory.updated_at = datetime.utcnow()
        updated_directory = self.directory_repository.save(directory)
        return self._to_dto(updated_directory)

    def delete_directory(
        self,
        directory_id: str,
        cascade: bool = False,
        force: bool = False,
        access_permissions: AccessPermissions = AccessPermissions(),
    ) -> None:
        """
        Delete a directory.

        Deletion modes:
        - Default (cascade=False, force=False): Only delete if empty (no subdirectories, no studies)
        - Cascade (cascade=True): Delete directory and all studies recursively
        - Force (force=True): Delete directory, studies become orphaned (directory_id = NULL)

        Args:
            directory_id: The directory ID to delete.
            cascade: If True, delete all studies in the directory recursively.
            force: If True, orphan studies instead of blocking deletion.
            access_permissions: User permissions.

        Raises:
            HTTPException: If directory not found, not empty, or no permission.
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Directory '{directory_id}' not found")

        if not self.directory_repository.has_permission(directory, access_permissions, write_access=True):
            raise UserHasNotPermissionError()

        # Check for subdirectories
        if self.directory_repository.has_children_directories(directory_id):
            if not (cascade or force):
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail="Cannot delete directory: it contains subdirectories. Use cascade=true or force=true.",
                )

            if cascade:
                # Recursively delete subdirectories
                self._delete_subdirectories_recursive(directory_id, access_permissions)
            elif force:
                # Orphan subdirectories by setting their parent_id to NULL
                self._orphan_subdirectories(directory_id)

        # Check for studies
        study_count = self.directory_repository.count_studies(directory_id)
        if study_count > 0:
            if not (cascade or force):
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"Cannot delete directory: it contains {study_count} studies. "
                    f"Use cascade=true to delete them or force=true to orphan them.",
                )

            if cascade:
                # Delete all studies in the directory
                self._delete_studies_in_directory(directory_id)

            # If force=true, studies will be orphaned automatically by ON DELETE SET NULL

        # Delete the directory
        self.directory_repository.delete(directory_id)

    def list_studies_in_directory(
        self,
        directory_id: str,
        access_permissions: AccessPermissions,
    ) -> List[StudyMetadataDTO]:
        """
        List all studies in a directory.

        Args:
            directory_id: The directory ID.
            access_permissions: User permissions.

        Returns:
            List of study metadata DTOs.

        Raises:
            HTTPException: If directory not found or no permission.
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Directory '{directory_id}' not found")

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        # Use study repository to get all studies
        study_filter = StudyFilter(access_permissions=access_permissions)
        all_studies = self.study_repository.get_all(study_filter)

        # Filter by directory_id and convert to DTOs
        studies_in_dir = [study for study in all_studies if study.directory_id == directory_id]

        # Convert to DTOs
        result = []
        for study in studies_in_dir:
            additional_data = study.additional_data or StudyAdditionalData()
            study_workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
            folder = getattr(study, "folder", None)

            owner_info = (
                OwnerInfo(id=study.owner.id, name=study.owner.name)
                if study.owner is not None
                else OwnerInfo(name=additional_data.author or "Unknown")
            )

            dto = StudyMetadataDTO(
                id=study.id,
                name=study.name,
                version=study.version,
                author=additional_data.author,
                editor=additional_data.editor,
                created=str(study.created_at),
                updated=str(study.updated_at),
                workspace=study_workspace,
                managed=study_workspace == DEFAULT_WORKSPACE_NAME,
                type=study.type,
                archived=study.archived if study.archived is not None else False,
                owner=owner_info,
                groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
                public_mode=study.public_mode or PublicMode.NONE,
                horizon=additional_data.horizon,
                folder=folder,
                tags=[tag.label for tag in study.tags],
            )
            result.append(dto)

        return result

    def _orphan_subdirectories(self, directory_id: str) -> None:
        """
        Orphan all direct subdirectories by setting their parent_id to NULL.

        Args:
            directory_id: Parent directory ID.
        """
        session = self.directory_repository.session
        stmt = update(Directory).where(Directory.parent_id == directory_id).values(parent_id=None)
        session.execute(stmt)
        session.commit()

    def _delete_subdirectories_recursive(self, directory_id: str, access_permissions: AccessPermissions) -> None:
        """
        Recursively delete all subdirectories and their studies.

        Args:
            directory_id: Parent directory ID.
            access_permissions: User permissions.
        """
        # Get direct children only (optimized: no longer fetches all directories)
        children = self.directory_repository.get_children(directory_id, access_permissions)

        for child in children:
            # Recursively delete subdirectories
            self._delete_subdirectories_recursive(child.id, access_permissions)
            # Delete studies in this child directory
            self._delete_studies_in_directory(child.id)
            # Delete the child directory itself
            self.directory_repository.delete(child.id)

    def _delete_studies_in_directory(self, directory_id: str) -> None:
        """
        Delete all studies in a specific directory.

        Args:
            directory_id: The directory ID whose studies should be deleted.
        """
        # Get studies in this directory only (optimized: filter by directory_id directly)
        study_filter = StudyFilter(directory_id=directory_id)
        studies_in_dir = self.study_repository.get_all(study_filter)

        # Delete each study using StudyService
        for study in studies_in_dir:
            try:
                # Delete study and its children (variants)
                self.study_service.delete_study(study.id, children=True)
            except Exception as e:
                # Log error but continue with other studies
                # This ensures partial failure doesn't stop the whole process
                logger.error(f"Failed to delete study {study.id} during cascade delete: {e}")

    def _to_dto(self, directory: Directory) -> DirectoryDTO:
        """
        Convert a Directory entity to a DirectoryDTO.

        Args:
            directory: The directory entity.

        Returns:
            Directory DTO.
        """
        owner_info = OwnerInfo(id=directory.owner_id, name=directory.owner.name if directory.owner else "Unknown")

        return DirectoryDTO(
            id=directory.id,
            name=directory.name,
            parent_id=directory.parent_id,
            owner=owner_info,
            groups=[GroupDTO(id=g.id, name=g.name) for g in directory.groups],
            created_at=directory.created_at.isoformat() if directory.created_at else "",
            updated_at=directory.updated_at.isoformat() if directory.updated_at else "",
        )
