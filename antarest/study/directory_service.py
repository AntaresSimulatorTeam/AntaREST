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
import uuid
from typing import TYPE_CHECKING, List, Sequence

from antarest.core.requests import UserHasNotPermissionError
from antarest.login.model import Group, GroupDTO
from antarest.study.directory_exceptions import (
    DirectoryAlreadyExistsError,
    DirectoryCycleError,
    DirectoryNotEmptyError,
    DirectoryNotFoundError,
    DirectoryPermissionError,
)
from antarest.study.model import (
    Directory,
    DirectoryCreation,
    DirectoryMetadata,
    DirectoryUpdate,
    OwnerInfo,
)
from antarest.study.repository import AccessPermissions, DirectoryRepository, StudyMetadataRepository

if TYPE_CHECKING:
    from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class DirectoryService:
    """Service for managing directories."""

    def __init__(
        self,
        directory_repository: DirectoryRepository,
        study_repository: StudyMetadataRepository,
        study_service: "StudyService",
    ):
        self.directory_repository = directory_repository
        self.study_repository = study_repository
        self.study_service = study_service

    def list_directories(self, access_permissions: AccessPermissions) -> List[DirectoryMetadata]:
        """List all directories the user has access to."""
        directories = self.directory_repository.get_all(access_permissions)
        return [self._to_dto(directory) for directory in directories]

    def create_directory(
        self,
        data: DirectoryCreation,
        owner_id: int,
        group_ids: Sequence[str],
        access_permissions: AccessPermissions,
    ) -> DirectoryMetadata:
        if data.parent_id:
            parent = self.directory_repository.get(data.parent_id)
            if parent is None:
                raise DirectoryNotFoundError(data.parent_id)

            if not self.directory_repository.has_permission(parent, access_permissions):
                raise DirectoryPermissionError("You don't have permission to create directories in this parent")

        if self.directory_repository.has_duplicate_name(data.name, data.parent_id):
            raise DirectoryAlreadyExistsError(data.name)

        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
            owner_id=owner_id,
        )

        session = self.directory_repository.session
        directory.groups = [session.get(Group, gid) for gid in group_ids if session.get(Group, gid)]

        saved_directory = self.directory_repository.save(directory)
        return self._to_dto(saved_directory)

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdate,
        access_permissions: AccessPermissions,
    ) -> DirectoryMetadata:
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        if data.name is not None and data.name != directory.name:
            if self.directory_repository.has_duplicate_name(data.name, directory.parent_id):
                raise DirectoryAlreadyExistsError(data.name)
            directory.name = data.name

        if data.parent_id is not None:
            if self.directory_repository.check_cycle(directory_id, data.parent_id):
                raise DirectoryCycleError()

            if data.parent_id != "":
                new_parent = self.directory_repository.get(data.parent_id)
                if new_parent is None:
                    raise DirectoryNotFoundError(data.parent_id)

                if not self.directory_repository.has_permission(new_parent, access_permissions):
                    raise DirectoryPermissionError("You don't have permission to move directories to this parent")

            directory.parent_id = data.parent_id if data.parent_id != "" else None

        if data.groups is not None:
            # Update groups: replace existing groups with the new list
            session = self.directory_repository.session
            directory.groups = [session.get(Group, gid) for gid in data.groups if session.get(Group, gid)]

        updated_directory = self.directory_repository.save(directory)
        return self._to_dto(updated_directory)

    def delete_directory(
        self,
        directory_id: str,
        access_permissions: AccessPermissions = AccessPermissions(),
    ) -> None:
        """
        Delete a directory only if it and all its subdirectories contain no studies.
        Empty subdirectories are deleted recursively along with the parent.
        All deletions are performed in a single transaction for consistency.
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        # Check if directory or any subdirectory contains studies
        if self._has_studies_recursive(directory_id):
            raise DirectoryNotEmptyError("Cannot delete directory: it or one of its subdirectories contains studies.")

        # Collect all directories to delete (depth-first)
        # Use admin permissions to ensure we collect ALL subdirectories
        # This is necessary because we already verified the user has permission to delete the root directory
        directories_to_delete = self._collect_directories_to_delete(directory_id, AccessPermissions(is_admin=True))

        # Delete all directories in a single transaction
        self.directory_repository.delete_batch(directories_to_delete)

    def _has_studies_recursive(self, directory_id: str) -> bool:
        """Check if directory or any of its subdirectories contains studies."""
        # Check current directory
        if self.directory_repository.count_studies(directory_id) > 0:
            return True

        # Check all subdirectories recursively
        children = self.directory_repository.get_children(directory_id, AccessPermissions(is_admin=True))
        for child in children:
            if self._has_studies_recursive(child.id):
                return True

        return False

    def _collect_directories_to_delete(self, directory_id: str, access_permissions: AccessPermissions) -> List[str]:
        """
        Collect all directory IDs to delete in depth-first order.
        Returns a list with children before parents for proper deletion order.
        """
        directories_to_delete = []

        # Recursively collect all children first
        children = self.directory_repository.get_children(directory_id, access_permissions)
        for child in children:
            directories_to_delete.extend(self._collect_directories_to_delete(child.id, access_permissions))

        # Add the current directory after all its children
        directories_to_delete.append(directory_id)

        return directories_to_delete

    def _to_dto(self, directory: Directory) -> DirectoryMetadata:
        """Convert Directory entity to DTO."""
        owner_info = OwnerInfo(id=directory.owner_id, name=directory.owner.name if directory.owner else "Unknown")

        return DirectoryMetadata(
            id=directory.id,
            name=directory.name,
            parent_id=directory.parent_id,
            owner=owner_info,
            groups=[GroupDTO(id=g.id, name=g.name) for g in directory.groups],
        )
