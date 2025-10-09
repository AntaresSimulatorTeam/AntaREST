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
Unit tests for DirectoryService.

Tests the service layer business logic including:
- Directory creation with validation
- Permission checks
- Update operations
- Deletion modes (simple, cascade, force)
"""

import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.requests import UserHasNotPermissionError
from antarest.login.model import Group, Identity
from antarest.study.directory_service import DirectoryService
from antarest.study.model import Directory, DirectoryCreateDTO, DirectoryUpdateDTO
from antarest.study.repository import AccessPermissions, DirectoryRepository, StudyMetadataRepository


@pytest.fixture
def mock_directory_repo() -> Mock:
    """Create a mock directory repository."""
    return Mock(spec=DirectoryRepository)


@pytest.fixture
def mock_study_repo() -> Mock:
    """Create a mock study repository."""
    return Mock(spec=StudyMetadataRepository)


@pytest.fixture
def mock_study_service() -> Mock:
    """Create a mock study service."""
    from antarest.study.service import StudyService

    return Mock(spec=StudyService)


@pytest.fixture
def directory_service(mock_directory_repo: Mock, mock_study_repo: Mock, mock_study_service: Mock) -> DirectoryService:
    """Create a directory service with mock repositories and study service."""
    return DirectoryService(
        directory_repository=mock_directory_repo,
        study_repository=mock_study_repo,
        study_service=mock_study_service,
    )


@pytest.fixture
def test_user() -> Identity:
    """Create a test user."""
    return Identity(id=1, name="test_user")


@pytest.fixture
def test_group() -> Group:
    """Create a test group."""
    return Group(id="test-group", name="Test Group")


class TestDirectoryService:
    """Unit tests for DirectoryService."""

    def test_create_directory_success(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
        test_group: Group,
    ) -> None:
        """
        Test successful directory creation.
        """
        # Setup
        data = DirectoryCreateDTO(name="New Directory", parent_id=None)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = Directory(
            id=str(uuid.uuid4()),
            name="New Directory",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_directory_repo.session.get.return_value = test_group

        # Execute
        result = directory_service.create_directory(data, test_user.id, [test_group.id], access_permissions)

        # Verify
        assert result.name == "New Directory"
        mock_directory_repo.has_duplicate_name.assert_called_once_with("New Directory", None)
        mock_directory_repo.save.assert_called_once()

    def test_create_directory_with_parent_not_found(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that creating a directory with non-existent parent fails.
        """
        # Setup
        fake_parent_id = str(uuid.uuid4())
        data = DirectoryCreateDTO(name="Child Directory", parent_id=fake_parent_id)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, [], access_permissions)

        assert exc_info.value.status_code == 404
        assert fake_parent_id in str(exc_info.value.detail)

    def test_create_directory_no_permission_on_parent(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that creating directory in parent without permission fails.
        """
        # Setup
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
            owner_id=2,  # Different owner
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        data = DirectoryCreateDTO(name="Child", parent_id=parent.id)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = parent
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, [], access_permissions)

        assert exc_info.value.status_code == 403

    def test_create_directory_duplicate_name(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that creating directory with duplicate name fails.
        """
        # Setup
        data = DirectoryCreateDTO(name="Duplicate", parent_id=None)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.has_duplicate_name.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, [], access_permissions)

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)

    def test_update_directory_name(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test updating directory name.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Old Name",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        data = DirectoryUpdateDTO(name="New Name")
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = existing_directory

        # Execute
        directory_service.update_directory(directory_id, data, access_permissions)

        # Verify
        assert existing_directory.name == "New Name"
        mock_directory_repo.save.assert_called_once()

    def test_update_directory_not_found(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test updating non-existent directory fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        data = DirectoryUpdateDTO(name="New Name")
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data, access_permissions)

        assert exc_info.value.status_code == 404

    def test_update_directory_no_permission(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test updating directory without permission fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=2,  # Different owner
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        data = DirectoryUpdateDTO(name="New Name")
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(UserHasNotPermissionError):
            directory_service.update_directory(directory_id, data, access_permissions)

    def test_update_directory_cycle_detection(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that moving directory to create cycle is prevented.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        new_parent_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        data = DirectoryUpdateDTO(parent_id=new_parent_id)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.check_cycle.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data, access_permissions)

        assert exc_info.value.status_code == 400
        assert "cycle" in str(exc_info.value.detail)

    def test_delete_empty_directory(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test deleting an empty directory.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Empty Directory",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_children_directories.return_value = False
        mock_directory_repo.count_studies.return_value = 0

        # Execute
        directory_service.delete_directory(
            directory_id, cascade=False, force=False, access_permissions=access_permissions
        )

        # Verify
        mock_directory_repo.delete.assert_called_once_with(directory_id)

    def test_delete_non_empty_directory_without_flags(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that deleting non-empty directory without cascade/force fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Non-Empty Directory",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_children_directories.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.delete_directory(
                directory_id, cascade=False, force=False, access_permissions=access_permissions
            )

        assert exc_info.value.status_code == 409
        assert "subdirectories" in str(exc_info.value.detail)

    def test_delete_directory_with_studies_without_flags(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test that deleting directory with studies without cascade/force fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory with Studies",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_children_directories.return_value = False
        mock_directory_repo.count_studies.return_value = 5

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.delete_directory(
                directory_id, cascade=False, force=False, access_permissions=access_permissions
            )

        assert exc_info.value.status_code == 409
        assert "5 studies" in str(exc_info.value.detail)

    def test_delete_directory_with_force(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test deleting directory with force flag (orphans studies).
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory with Studies",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_children_directories.return_value = False
        mock_directory_repo.count_studies.return_value = 3

        # Execute
        directory_service.delete_directory(
            directory_id, cascade=False, force=True, access_permissions=access_permissions
        )

        # Verify - directory should be deleted, studies orphaned by DB constraint
        mock_directory_repo.delete.assert_called_once_with(directory_id)

    def test_delete_directory_with_cascade(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        mock_study_repo: Mock,
        mock_study_service: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test deleting directory with cascade flag (deletes studies).
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory with Studies",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        # Mock studies in directory
        from antarest.study.model import Study, StudyAdditionalData

        study1 = Study(
            id="study1",
            name="Study 1",
            directory_id=directory_id,
            additional_data=StudyAdditionalData(),
        )
        study2 = Study(
            id="study2",
            name="Study 2",
            directory_id=directory_id,
            additional_data=StudyAdditionalData(),
        )

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_children_directories.return_value = False
        mock_directory_repo.count_studies.return_value = 2

        # Mock study repository to return studies in directory

        mock_study_repo.get_all.return_value = [study1, study2]

        # Execute
        directory_service.delete_directory(
            directory_id, cascade=True, force=False, access_permissions=access_permissions
        )

        # Verify - studies should be deleted, then directory
        mock_study_service.delete_study.assert_any_call("study1", children=True)
        mock_study_service.delete_study.assert_any_call("study2", children=True)
        assert mock_study_service.delete_study.call_count == 2
        mock_directory_repo.delete.assert_called_once_with(directory_id)

    def test_delete_directory_no_permission(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test deleting directory without permission fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=2,  # Different owner
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(UserHasNotPermissionError):
            directory_service.delete_directory(
                directory_id, cascade=False, force=False, access_permissions=access_permissions
            )

    def test_get_directory_success(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test getting directory with permission.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Test Directory",
            parent_id=None,
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        directory.owner = test_user
        directory.groups = []
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True

        # Execute
        result = directory_service.get_directory(directory_id, access_permissions)

        # Verify
        assert result.id == directory_id
        assert result.name == "Test Directory"

    def test_get_directory_not_found(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test getting non-existent directory fails.
        """
        # Setup
        directory_id = str(uuid.uuid4())
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])

        mock_directory_repo.get.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.get_directory(directory_id, access_permissions)

        assert exc_info.value.status_code == 404

    def test_list_directories(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        """
        Test listing directories.
        """
        # Setup
        directories = [
            Directory(
                id=str(uuid.uuid4()),
                name=f"Directory {i}",
                parent_id=None,
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(3)
        ]
        for d in directories:
            d.owner = test_user
            d.groups = []

        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])
        mock_directory_repo.get_all.return_value = directories

        # Execute
        result = directory_service.list_directories(access_permissions)

        # Verify
        assert len(result) == 3
        mock_directory_repo.get_all.assert_called_once_with(access_permissions)
