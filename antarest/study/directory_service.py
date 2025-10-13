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

"""Service layer for Directory management."""

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Sequence

from sqlalchemy import update

from antarest.core.model import PublicMode
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

    def list_directories(self, access_permissions: AccessPermissions) -> List[DirectoryDTO]:
        """List all directories the user has access to."""
        directories = self.directory_repository.get_all(access_permissions)
        return [self._to_dto(directory) for directory in directories]

    def get_directory(self, directory_id: str, access_permissions: AccessPermissions) -> DirectoryDTO:
        """Get a directory by ID."""
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

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
        """Create a new directory."""
        if data.parent_id:
            parent = self.directory_repository.get(data.parent_id)
            if parent is None:
                raise DirectoryNotFoundError(data.parent_id)

            if not self.directory_repository.has_permission(parent, access_permissions, write_access=True):
                raise DirectoryPermissionError("You don't have permission to create directories in this parent")

        if self.directory_repository.has_duplicate_name(data.name, data.parent_id):
            raise DirectoryAlreadyExistsError(data.name)

        directory = Directory(
            id=str(uuid.uuid4()),
            name=data.name,
            parent_id=data.parent_id,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session = self.directory_repository.session
        directory.groups = [session.get(Group, gid) for gid in group_ids if session.get(Group, gid)]

        saved_directory = self.directory_repository.save(directory)
        return self._to_dto(saved_directory)

    def update_directory(
        self,
        directory_id: str,
        data: DirectoryUpdateDTO,
        access_permissions: AccessPermissions,
    ) -> DirectoryDTO:
        """Update a directory (name or parent)."""
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions, write_access=True):
            raise UserHasNotPermissionError()

        if data.name is not None:
            if self.directory_repository.has_duplicate_name(data.name, directory.parent_id, exclude_id=directory_id):
                raise DirectoryAlreadyExistsError(data.name)
            directory.name = data.name

        if data.parent_id is not None:
            if self.directory_repository.check_cycle(directory_id, data.parent_id):
                raise DirectoryCycleError()

            if data.parent_id != "":
                new_parent = self.directory_repository.get(data.parent_id)
                if new_parent is None:
                    raise DirectoryNotFoundError(data.parent_id)

                if not self.directory_repository.has_permission(new_parent, access_permissions, write_access=True):
                    raise DirectoryPermissionError("You don't have permission to move directories to this parent")

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
        - cascade=True: delete all subdirectories and studies
        - force=True: orphan subdirectories and studies
        """
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions, write_access=True):
            raise UserHasNotPermissionError()

        if self.directory_repository.has_children_directories(directory_id):
            if not (cascade or force):
                raise DirectoryNotEmptyError(
                    "Cannot delete directory: it contains subdirectories. Use cascade=true or force=true."
                )

            if cascade:
                self._delete_children_recursive(directory_id, access_permissions)
            elif force:
                self._orphan_subdirectories(directory_id)

        study_count = self.directory_repository.count_studies(directory_id)
        if study_count > 0:
            if not (cascade or force):
                raise DirectoryNotEmptyError(
                    f"Cannot delete directory: it contains {study_count} studies. "
                    f"Use cascade=true to delete them or force=true to orphan them."
                )

            if cascade:
                self._delete_studies_in_directory(directory_id)

        # TODO: may need to handle outputs cleanup in cascade mode
        self.directory_repository.delete(directory_id)

    def list_studies_in_directory(
        self,
        directory_id: str,
        access_permissions: AccessPermissions,
    ) -> List[StudyMetadataDTO]:
        """List all studies in a directory."""
        directory = self.directory_repository.get(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(directory_id)

        if not self.directory_repository.has_permission(directory, access_permissions):
            raise UserHasNotPermissionError()

        study_filter = StudyFilter(access_permissions=access_permissions)
        all_studies = self.study_repository.get_all(study_filter)
        studies_in_dir = [study for study in all_studies if study.directory_id == directory_id]

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
        """Set parent_id to NULL for all subdirectories."""
        session = self.directory_repository.session
        stmt = update(Directory).where(Directory.parent_id == directory_id).values(parent_id=None)
        session.execute(stmt)
        session.commit()

    def _delete_children_recursive(self, directory_id: str, access_permissions: AccessPermissions) -> None:
        """Recursively delete all subdirectories and their studies."""
        children = self.directory_repository.get_children(directory_id, access_permissions)

        for child in children:
            self._delete_children_recursive(child.id, access_permissions)
            self._delete_studies_in_directory(child.id)
            self.directory_repository.delete(child.id)

    def _delete_studies_in_directory(self, directory_id: str) -> None:
        """Delete all studies in a directory."""
        study_filter = StudyFilter(directory_id=directory_id)
        studies = self.study_repository.get_all(study_filter)

        for study in studies:
            try:
                # delete with children to handle variants
                self.study_service.delete_study(study.id, children=True)
            except Exception as e:
                logger.error(f"Failed to delete study {study.id} during cascade: {e}")

    def _to_dto(self, directory: Directory) -> DirectoryDTO:
        """Convert Directory entity to DTO."""
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
