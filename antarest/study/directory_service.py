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
import uuid
from pathlib import PurePosixPath

from antarest.core.model import StudyPermissionType
from antarest.study.directory_exceptions import (
    DirectoryAlreadyExistsError,
    DirectoryCycleError,
    DirectoryNotEmptyError,
    DirectoryNotFoundError,
)
from antarest.study.model import (
    Directory,
    DirectoryCreation,
    DirectoryMetadata,
    DirectoryUpdate,
)
from antarest.study.repository import DirectoryRepository
from antarest.study.storage.utils import assert_permission

logger = logging.getLogger(__name__)


class DirectoryService:
    """Service for managing directories."""

    def __init__(
        self,
        directory_repository: DirectoryRepository,
    ):
        self.repository = directory_repository

    def list_directories(self) -> list[DirectoryMetadata]:
        directories = self.repository.get_all()
        return [directory.to_metadata() for directory in directories]

    def create_directory(
        self,
        data: DirectoryCreation,
    ) -> DirectoryMetadata:
        if data.parent_id:
            parent = self.repository.get_by_id(data.parent_id)
            if parent is None:
                raise DirectoryNotFoundError(data.parent_id)

        if self.repository.exists(data.name, data.parent_id):
            raise DirectoryAlreadyExistsError(data.name)

        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
        )

        logger.info(f"Creating directory '{data.name}' under parent '{data.parent_id}'")
        saved_directory = self.repository.save(directory)
        return saved_directory.to_metadata()

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdate,
    ) -> DirectoryMetadata:
        directory = self.repository.get_by_id(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        # Check permissions on all studies in the tree
        self._check_permissions_for_tree(directory_id)

        # Update parent first, then validate name in the target parent
        new_parent_id = directory.parent_id  # Keep current parent by default

        if data.parent_id is not None:
            if data.parent_id:  # Non-empty string
                if self.repository.check_cycle(directory_id, data.parent_id):
                    raise DirectoryCycleError()

                new_parent = self.repository.get_by_id(data.parent_id)
                if new_parent is None:
                    raise DirectoryNotFoundError(data.parent_id)

                new_parent_id = data.parent_id
            else:
                # Empty string means move to root
                new_parent_id = None

        # Validate name uniqueness in the target parent (current or new)
        if data.name is not None and data.name != directory.name:
            if self.repository.exists(data.name, new_parent_id):
                raise DirectoryAlreadyExistsError(data.name)
            directory.name = data.name

        # Apply parent change if any
        if data.parent_id is not None:
            directory.parent_id = new_parent_id

        updated_directory = self.repository.save(directory)
        return updated_directory.to_metadata()

    def delete_directory(
        self,
        directory_id: str,
    ) -> None:
        """
        Delete a directory only if it contains no studies (even in subdirectories).
        """
        if not self.repository.exists_by_id(directory_id):
            raise DirectoryNotFoundError(directory_id)

        if self.repository.count_studies_in_tree(directory_id) > 0:
            raise DirectoryNotEmptyError("Cannot delete directory: it contains studies.")

        # Delete the directory
        self.repository.delete(directory_id)

    def get_directory_by_path(self, folder_path: str) -> str | None:
        """
        Get or create directory ID from a folder path.
        Creates missing directories automatically with the specified owner and groups.

        Args:
            folder_path: POSIX folder path like "project/subfolder"

        Returns:
            Directory ID of the leaf directory, or None if path is empty
        """
        if not folder_path:
            return None

        path = PurePosixPath(folder_path)

        if not path.parts:
            return None

        # Navigate/create directory hierarchy
        parent_id = None
        for dir_name in path.parts:
            existing_dir = self.repository.get_by_name(dir_name, parent_id)

            if not existing_dir:
                new_dir = Directory(
                    id=str(uuid.uuid4()),
                    name=dir_name,
                    parent_id=parent_id,
                )
                self.repository.save(new_dir)
                parent_id = new_dir.id
            else:
                parent_id = existing_dir.id

        return parent_id

    def get_directory_paths_bulk(self, directory_ids: list[str]) -> dict[str, str]:
        """
        Get directory paths for multiple directory IDs in bulk using a single CTE query.

        Args:
            directory_ids: List of directory IDs

        Returns:
            Dictionary mapping directory_id -> folder_path (e.g., {"dir-123": "parent/child"})
        """
        if not directory_ids:
            return {}

        return self.repository.get_directory_paths_bulk(directory_ids)

    def _has_studies(self, directory_id: str) -> bool:
        return self.repository.count_studies(directory_id) > 0

    def _check_permissions_for_tree(self, directory_id: str) -> None:
        """
        Check that user has permissions on all studies in the tree.

        Args:
            directory_id: The root directory ID to check

        Raises:
            UserHasNotPermissionError: If user doesn't have permission on any study
        """
        studies = self.repository.get_all_studies_in_tree(directory_id)
        for study in studies:
            assert_permission(study, StudyPermissionType.WRITE)
