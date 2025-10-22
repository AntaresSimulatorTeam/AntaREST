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

import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.requests import UserHasNotPermissionError
from antarest.login.model import Group, Identity
from antarest.login.repository import GroupRepository
from antarest.study.directory_service import DirectoryService
from antarest.study.model import Directory, DirectoryCreation, DirectoryUpdate
from antarest.study.repository import DirectoryRepository, StudyMetadataRepository


@pytest.fixture
def mock_directory_repo() -> Mock:
    return Mock(spec=DirectoryRepository)


@pytest.fixture
def mock_study_repo() -> Mock:
    return Mock(spec=StudyMetadataRepository)


@pytest.fixture
def mock_study_service() -> Mock:
    from antarest.study.service import StudyService

    return Mock(spec=StudyService)


@pytest.fixture
def mock_group_repo() -> Mock:
    return Mock(spec=GroupRepository)


@pytest.fixture
def directory_service(
    mock_directory_repo: Mock, mock_study_repo: Mock, mock_study_service: Mock, mock_group_repo: Mock
) -> DirectoryService:
    return DirectoryService(
        directory_repository=mock_directory_repo,
        study_repository=mock_study_repo,
        study_service=mock_study_service,
        group_repository=mock_group_repo,
    )


@pytest.fixture
def test_user() -> Identity:
    return Identity(id=1, name="test_user")


@pytest.fixture
def test_group() -> Group:
    return Group(id="test-group", name="Test Group")


class TestDirectoryService:
    def test_create_directory_success(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        mock_group_repo: Mock,
        test_user: Identity,
        test_group: Group,
    ) -> None:
        # Setup
        data = DirectoryCreation(name="New Directory", parent_id=None)

        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = Directory(
            id=str(uuid.uuid4()),
            name="New Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_group_repo.get_by_ids.return_value = [test_group]

        # Execute
        result = directory_service.create_directory(data, test_user.id, default_group_ids=[test_group.id])

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
        # Setup
        fake_parent_id = str(uuid.uuid4())
        data = DirectoryCreation(name="Child Directory", parent_id=fake_parent_id)

        mock_directory_repo.get.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, default_group_ids=[])

        assert exc_info.value.status_code == 404
        assert fake_parent_id in str(exc_info.value.detail)

    def test_create_directory_no_permission_on_parent(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
            owner_id=2,  # Different owner
        )
        data = DirectoryCreation(name="Child", parent_id=parent.id)

        mock_directory_repo.get.return_value = parent
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, default_group_ids=[])

        assert exc_info.value.status_code == 403

    def test_create_directory_duplicate_name(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        data = DirectoryCreation(name="Duplicate", parent_id=None)

        mock_directory_repo.has_duplicate_name.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data, test_user.id, default_group_ids=[])

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)

    def test_create_directory_uses_default_groups_when_not_specified(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        mock_group_repo: Mock,
        test_user: Identity,
        test_group: Group,
    ) -> None:
        # Setup - DirectoryCreation without groups specified
        data = DirectoryCreation(name="New Directory", parent_id=None, groups=None)
        default_group = Group(id="default-group", name="Default Group")

        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = Directory(
            id=str(uuid.uuid4()),
            name="New Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_group_repo.get_by_ids.return_value = [default_group]

        # Execute
        directory_service.create_directory(data, test_user.id, default_group_ids=[default_group.id])

        # Verify that default groups were used
        mock_group_repo.get_by_ids.assert_called_once_with([default_group.id])

    def test_create_directory_uses_specified_groups_over_defaults(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        mock_group_repo: Mock,
        test_user: Identity,
        test_group: Group,
    ) -> None:
        # Setup - DirectoryCreation with explicit groups
        specified_group = Group(id="specified-group", name="Specified Group")
        data = DirectoryCreation(name="New Directory", parent_id=None, groups=[specified_group.id])
        default_group = Group(id="default-group", name="Default Group")

        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = Directory(
            id=str(uuid.uuid4()),
            name="New Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_group_repo.get_by_ids.return_value = [specified_group]

        # Execute
        directory_service.create_directory(data, test_user.id, default_group_ids=[default_group.id])

        # Verify that specified groups were used, not defaults
        mock_group_repo.get_by_ids.assert_called_once_with([specified_group.id])

    def test_update_directory_name(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Old Name",
            owner_id=test_user.id,
        )
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.has_duplicate_name.return_value = False
        mock_directory_repo.save.return_value = existing_directory

        # Execute
        directory_service.update_directory(directory_id, data)

        # Verify
        assert existing_directory.name == "New Name"
        mock_directory_repo.save.assert_called_once()

    def test_update_directory_not_found(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data)

        assert exc_info.value.status_code == 404

    def test_update_directory_no_permission(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=2,  # Different owner
        )
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(UserHasNotPermissionError):
            directory_service.update_directory(directory_id, data)

    def test_update_directory_cycle_detection(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        new_parent_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        data = DirectoryUpdate(parent_id=new_parent_id)

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.check_cycle.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data)

        assert exc_info.value.status_code == 400
        assert "cycle" in str(exc_info.value.detail)

    def test_update_directory_groups(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        mock_group_repo: Mock,
        test_user: Identity,
        test_group: Group,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        new_group = Group(id="new-group", name="New Group")
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        existing_directory.groups = [test_group]  # Initially has test_group

        data = DirectoryUpdate(groups=[new_group.id])  # Update to new_group

        mock_directory_repo.get.return_value = existing_directory
        mock_directory_repo.has_permission.return_value = True
        mock_group_repo.get_by_ids.return_value = [new_group]
        mock_directory_repo.save.return_value = existing_directory

        # Execute
        directory_service.update_directory(directory_id, data)

        # Verify groups were updated
        mock_group_repo.get_by_ids.assert_called_once_with([new_group.id])
        mock_directory_repo.save.assert_called_once()

    def test_delete_empty_directory(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Empty Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.count_studies.return_value = 0
        mock_directory_repo.has_children_directories.return_value = False

        # Execute
        directory_service.delete_directory(directory_id)

        # Verify
        mock_directory_repo.delete.assert_called_once_with(directory_id)

    def test_delete_directory_with_subdirectories_fails(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Parent Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.count_studies.return_value = 0
        mock_directory_repo.has_children_directories.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.delete_directory(directory_id)

        assert exc_info.value.status_code == 409
        assert "subdirectories" in str(exc_info.value.detail).lower()

    def test_delete_directory_with_studies_fails(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory with Studies",
            parent_id=None,
            owner_id=test_user.id,
        )
        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = True
        mock_directory_repo.count_studies.return_value = 5
        mock_directory_repo.has_children_directories.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.delete_directory(directory_id)

        assert exc_info.value.status_code == 409
        assert "studies" in str(exc_info.value.detail).lower()

    def test_delete_directory_no_permission(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
            owner_id=2,  # Different owner
        )
        mock_directory_repo.get.return_value = directory
        mock_directory_repo.has_permission.return_value = False

        # Execute & Verify
        with pytest.raises(UserHasNotPermissionError):
            directory_service.delete_directory(directory_id)

    def test_list_directories(
        self,
        directory_service: DirectoryService,
        mock_directory_repo: Mock,
        test_user: Identity,
    ) -> None:
        # Setup
        directories = [
            Directory(
                id=str(uuid.uuid4()),
                name=f"Directory {i}",
                parent_id=None,
                owner_id=test_user.id,
            )
            for i in range(3)
        ]
        for d in directories:
            d.owner = test_user
            d.groups = []

        mock_directory_repo.get_all.return_value = directories

        # Execute
        result = directory_service.list_directories()

        # Verify
        assert len(result) == 3
