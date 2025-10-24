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

import pytest
from sqlalchemy.orm import Session

from antarest.login.model import Identity
from antarest.study.model import Directory
from antarest.study.repository import DirectoryRepository


@pytest.fixture
def directory_repo(db_session: Session) -> DirectoryRepository:
    return DirectoryRepository(session=db_session)


@pytest.fixture
def test_user(db_session: Session) -> Identity:
    user = Identity(id=1, name="test_user")
    db_session.add(user)
    db_session.commit()
    return user


class TestDirectoryRepository:
    def test_save_and_get_directory(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Test Directory",
            parent_id=None,
        )

        # Save
        saved = directory_repo.save(directory)
        assert saved.id == directory.id
        assert saved.name == "Test Directory"

        # Retrieve
        retrieved = directory_repo.get_by_id(directory.id)
        assert retrieved is not None
        assert retrieved.id == directory.id
        assert retrieved.name == "Test Directory"

    def test_get_all_directories(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        for i in range(3):
            directory = Directory(
                id=str(uuid.uuid4()),
                name=f"Directory {i}",
                parent_id=None,
            )
            directory_repo.save(directory)

        directories = directory_repo.get_all()
        assert len(directories) >= 3

    def test_delete_directory(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="To Delete",
            parent_id=None,
        )
        directory_repo.save(directory)

        # Verify exists
        assert directory_repo.get_by_id(directory.id) is not None

        # Delete
        directory_repo.delete(directory.id)

        # Verify deleted
        assert directory_repo.get_by_id(directory.id) is None

    def test_check_cycle_self(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        directory_id = str(uuid.uuid4())
        assert directory_repo.check_cycle(directory_id, directory_id)

    def test_check_cycle_simple(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create A
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
        )
        directory_repo.save(dir_a)

        # Create B with A as parent
        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=dir_a.id,
        )
        directory_repo.save(dir_b)

        # Try to make A a child of B (would create cycle)
        assert directory_repo.check_cycle(dir_a.id, dir_b.id)

    def test_check_cycle_deep(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create A -> B -> C
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
        )
        directory_repo.save(dir_a)

        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=dir_a.id,
        )
        directory_repo.save(dir_b)

        dir_c = Directory(
            id=str(uuid.uuid4()),
            name="C",
            parent_id=dir_b.id,
        )
        directory_repo.save(dir_c)

        # Try to make A a child of C (would create cycle)
        assert directory_repo.check_cycle(dir_a.id, dir_c.id)

    def test_check_cycle_no_cycle(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create A and B (siblings)
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
        )
        directory_repo.save(dir_a)

        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=None,
        )
        directory_repo.save(dir_b)

        # Create C under A
        dir_c = Directory(
            id=str(uuid.uuid4()),
            name="C",
            parent_id=dir_a.id,
        )
        directory_repo.save(dir_c)

        # Move C under B (no cycle)
        assert not directory_repo.check_cycle(dir_c.id, dir_b.id)

    def test_has_duplicate_name_same_parent(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        # Create parent
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
        )
        directory_repo.save(parent)

        # Create child
        child = Directory(
            id=str(uuid.uuid4()),
            name="Child",
            parent_id=parent.id,
        )
        directory_repo.save(child)

        # Check for duplicate (should be true)
        assert directory_repo.exists("Child", parent.id)

    def test_has_duplicate_name_different_parent(
        self, directory_repo: DirectoryRepository, test_user: Identity
    ) -> None:
        # Create two parents
        parent1 = Directory(
            id=str(uuid.uuid4()),
            name="Parent1",
            parent_id=None,
        )
        directory_repo.save(parent1)

        parent2 = Directory(
            id=str(uuid.uuid4()),
            name="Parent2",
            parent_id=None,
        )
        directory_repo.save(parent2)

        # Create child in parent1
        child = Directory(
            id=str(uuid.uuid4()),
            name="SameName",
            parent_id=parent1.id,
        )
        directory_repo.save(child)

        # Check for duplicate in parent2 (should be false)
        assert not directory_repo.exists("SameName", parent2.id)

    def test_has_children_directories(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test checking if directory has children.
        """
        # Create parent
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
        )
        directory_repo.save(parent)

        # Initially no children
        assert not directory_repo.has_children_directories(parent.id)

        # Create child
        child = Directory(
            id=str(uuid.uuid4()),
            name="Child",
            parent_id=parent.id,
        )
        directory_repo.save(child)

        # Now has children
        assert directory_repo.has_children_directories(parent.id)

    def test_count_studies(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test counting studies in a directory.
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Study Directory",
            parent_id=None,
        )
        directory_repo.save(directory)

        # Count studies (should be 0 initially)
        count = directory_repo.count_studies(directory.id)
        assert count == 0
