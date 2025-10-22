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
from typing import List, Sequence

from antarest.core.requests import UserHasNotPermissionError
from antarest.login.repository import GroupRepository
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
)
from antarest.study.repository import AccessPermissions, DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class DirectoryService:
    """Service for managing directories."""

    def __init__(
        self,
        directory_repository: DirectoryRepository,
        study_repository: StudyMetadataRepository,
        study_service: StudyService,
        group_repository: GroupRepository,
    ):
        self.directory_repository = directory_repository
        self.study_repository = study_repository
        self.study_service = study_service
        self.group_repository = group_repository

    def list_directories(self) -> List[DirectoryMetadata]:
        """List all directories the user has access to."""
        access_permissions = AccessPermissions.for_current_user()
        directories = self.directory_repository.get_all(access_permissions)
        return [directory.to_metadata() for directory in directories]

    def create_directory(
        self,
        data: DirectoryCreation,
        owner_id: int,
        default_group_ids: Sequence[str],
    ) -> DirectoryMetadata:
        access_permissions = AccessPermissions.for_current_user()
        if data.parent_id:
            parent = self.directory_repository.get(data.parent_id)
            if parent is None:
                raise DirectoryNotFoundError(data.parent_id)

            if not self.directory_repository.has_permission(parent, access_permissions):
                raise DirectoryPermissionError("You don't have permission to create directories in this parent")

        if self.directory_repository.has_duplicate_name(data.name, data.parent_id):
            raise DirectoryAlreadyExistsError(data.name)

        # Use specified groups or fall back to user's default groups
        group_ids = data.groups if data.groups is not None else default_group_ids

        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
            owner_id=owner_id,
        )

        directory.groups = self.group_repository.get_by_ids(list(group_ids))

        saved_directory = self.directory_repository.save(directory)
        return saved_directory.to_metadata()

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdate,
    ) -> DirectoryMetadata:
        access_permissions = AccessPermissions.for_current_user()
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        # Update parent first, then validate name in the target parent
        new_parent_id = directory.parent_id  # Keep current parent by default

        if data.parent_id is not None:
            if data.parent_id:  # Non-empty string
                if self.directory_repository.check_cycle(directory_id, data.parent_id):
                    raise DirectoryCycleError()

                new_parent = self.directory_repository.get(data.parent_id)
                if new_parent is None:
                    raise DirectoryNotFoundError(data.parent_id)

                if not self.directory_repository.has_permission(new_parent, access_permissions):
                    raise DirectoryPermissionError("You don't have permission to move directories to this parent")

                new_parent_id = data.parent_id
            else:
                # Empty string means move to root
                new_parent_id = None

        # Validate name uniqueness in the target parent (current or new)
        if data.name is not None and data.name != directory.name:
            if self.directory_repository.has_duplicate_name(data.name, new_parent_id):
                raise DirectoryAlreadyExistsError(data.name)
            directory.name = data.name

        # Apply parent change if any
        if data.parent_id is not None:
            directory.parent_id = new_parent_id

        if data.groups is not None:
            # Update groups: replace existing groups with the new list
            directory.groups = self.group_repository.get_by_ids(data.groups)

        updated_directory = self.directory_repository.save(directory)
        return updated_directory.to_metadata()

    def delete_directory(
        self,
        directory_id: str,
    ) -> None:
        """
        Delete a directory only if it is completely empty (no studies and no subdirectories).
        """
        access_permissions = AccessPermissions.for_current_user()
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        # Check if directory contains studies
        if self._has_studies(directory_id):
            raise DirectoryNotEmptyError("Cannot delete directory: it contains studies.")

        # Check if directory contains subdirectories
        if self.directory_repository.has_children_directories(directory_id):
            raise DirectoryNotEmptyError("Cannot delete directory: it contains subdirectories.")

        # Delete the directory
        self.directory_repository.delete(directory_id)

    def _has_studies(self, directory_id: str) -> bool:
        """Check if directory contains studies."""
        return self.directory_repository.count_studies(directory_id) > 0
