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

import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.login.model import Identity
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
def directory_service(mock_directory_repo: Mock) -> DirectoryService:
    return DirectoryService(
        directory_repository=mock_directory_repo,
    )


@pytest.fixture
def test_user() -> Identity:
    return Identity(id=1, name="test_user")


class TestDirectoryService:
    def test_create_directory_success(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        data = DirectoryCreation(name="New Directory", parent_id=None)

        mock_directory_repo.exists.return_value = False
        mock_directory_repo.save.return_value = Directory(
            id=str(uuid.uuid4()),
            name="New Directory",
            parent_id=None,
        )

        # Execute
        result = directory_service.create_directory(data)

        # Verify
        assert result.name == "New Directory"
        mock_directory_repo.exists.assert_called_once_with("New Directory", None)
        mock_directory_repo.save.assert_called_once()

    def test_create_directory_with_parent_not_found(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        fake_parent_id = str(uuid.uuid4())
        data = DirectoryCreation(name="Child Directory", parent_id=fake_parent_id)

        mock_directory_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data)

        assert exc_info.value.status_code == 404
        assert fake_parent_id in str(exc_info.value.detail)

    def test_create_directory_duplicate_name(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        data = DirectoryCreation(name="Duplicate", parent_id=None)

        mock_directory_repo.exists.return_value = True

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.create_directory(data)

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)

    def test_update_directory_name(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Old Name",
        )
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get_by_id.return_value = existing_directory
        mock_directory_repo.exists.return_value = False
        mock_directory_repo.save.return_value = existing_directory
        mock_directory_repo.get_all_descendant_directories.return_value = []
        mock_directory_repo.get_all_studies_in_tree.return_value = []

        # Execute
        directory_service.update_directory(directory_id, data)

        # Verify
        assert existing_directory.name == "New Name"
        mock_directory_repo.save.assert_called_once()

    def test_update_directory_not_found(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data)

        assert exc_info.value.status_code == 404

    def test_update_directory_cycle_detection(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        new_parent_id = str(uuid.uuid4())
        existing_directory = Directory(
            id=directory_id,
            name="Directory",
            parent_id=None,
        )
        data = DirectoryUpdate(parent_id=new_parent_id)

        mock_directory_repo.get_by_id.return_value = existing_directory
        mock_directory_repo.check_cycle.return_value = True
        mock_directory_repo.get_all_descendant_directories.return_value = []
        mock_directory_repo.get_all_studies_in_tree.return_value = []

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data)

        assert exc_info.value.status_code == 400
        assert "cycle" in str(exc_info.value.detail)

    def test_delete_empty_directory(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())

        mock_directory_repo.exists_by_id.return_value = True
        mock_directory_repo.count_studies_in_tree.return_value = 0

        # Execute
        directory_service.delete_directory(directory_id)

        # Verify
        mock_directory_repo.delete.assert_called_once_with(directory_id)

    def test_delete_directory_with_studies_fails(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())

        mock_directory_repo.exists_by_id.return_value = True
        mock_directory_repo.count_studies_in_tree.return_value = 5

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.delete_directory(directory_id)

        assert exc_info.value.status_code == 409

    def test_list_directories(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directories = [
            Directory(
                id=str(uuid.uuid4()),
                name=f"Directory {i}",
                parent_id=None,
            )
            for i in range(3)
        ]

        mock_directory_repo.get_all.return_value = directories

        # Execute
        result = directory_service.list_directories()

        # Verify
        assert len(result) == 3

    def test_update_directory_tree_check_directory_not_found(
        self, directory_service: DirectoryService, mock_directory_repo: Mock, test_user: Identity
    ) -> None:
        # Setup
        directory_id = str(uuid.uuid4())
        data = DirectoryUpdate(name="New Name")

        mock_directory_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            directory_service.update_directory(directory_id, data)

        assert exc_info.value.status_code == 404
        assert directory_id in str(exc_info.value.detail)
