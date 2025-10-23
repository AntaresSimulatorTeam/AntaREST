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
from typing import List

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
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.utils import assert_permission

logger = logging.getLogger(__name__)


class DirectoryService:
    """Service for managing directories."""

    def __init__(
        self,
        directory_repository: DirectoryRepository,
        study_repository: StudyMetadataRepository,
        study_service: StudyService,
    ):
        self.directory_repository = directory_repository
        self.study_repository = study_repository
        self.study_service = study_service

    def list_directories(self) -> List[DirectoryMetadata]:
        directories = self.directory_repository.get_all()
        return [directory.to_metadata() for directory in directories]

    def create_directory(
        self,
        data: DirectoryCreation,
    ) -> DirectoryMetadata:
        if data.parent_id:
            parent = self.directory_repository.get(data.parent_id)
            if parent is None:
                raise DirectoryNotFoundError(data.parent_id)

        if self.directory_repository.has_duplicate_name(data.name, data.parent_id):
            raise DirectoryAlreadyExistsError(data.name)

        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
        )

        saved_directory = self.directory_repository.save(directory)
        return saved_directory.to_metadata()

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdate,
    ) -> DirectoryMetadata:
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        # Check permissions on all studies in the tree
        self._check_permissions_for_tree(directory_id)

        # Update parent first, then validate name in the target parent
        new_parent_id = directory.parent_id  # Keep current parent by default

        if data.parent_id is not None:
            if data.parent_id:  # Non-empty string
                if self.directory_repository.check_cycle(directory_id, data.parent_id):
                    raise DirectoryCycleError()

                new_parent = self.directory_repository.get(data.parent_id)
                if new_parent is None:
                    raise DirectoryNotFoundError(data.parent_id)

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

        updated_directory = self.directory_repository.save(directory)
        return updated_directory.to_metadata()

    def delete_directory(
        self,
        directory_id: str,
    ) -> None:
        """
        Delete a directory only if it is completely empty (no studies and no subdirectories).
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        # Check if directory contains studies
        if self._has_studies(directory_id):
            raise DirectoryNotEmptyError("Cannot delete directory: it contains studies.")

        # Check if directory contains subdirectories
        if self.directory_repository.has_children_directories(directory_id):
            raise DirectoryNotEmptyError("Cannot delete directory: it contains subdirectories.")

        # Delete the directory
        self.directory_repository.delete(directory_id)

    def _has_studies(self, directory_id: str) -> bool:
        return self.directory_repository.count_studies(directory_id) > 0

    def _check_permissions_for_tree(self, directory_id: str) -> None:
        """
        Check that user has permissions on all studies in the tree.

        Args:
            directory_id: The root directory ID to check

        Raises:
            UserHasNotPermissionError: If user doesn't have permission on any study
        """

        # Check all studies in the tree
        studies = self.directory_repository.get_all_studies_in_tree(directory_id)
        for study in studies:
            assert_permission(study, StudyPermissionType.READ)
