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
Unit tests for DirectoryRepository.

Tests the repository layer for directory management including:
- CRUD operations
- Permission checks
- Cycle detection
- Duplicate name validation
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from antarest.login.model import Group, Identity
from antarest.study.model import Directory
from antarest.study.repository import AccessPermissions, DirectoryRepository


@pytest.fixture
def directory_repo(db_session: Session) -> DirectoryRepository:
    """Create a directory repository for testing."""
    return DirectoryRepository(session=db_session)


@pytest.fixture
def test_user(db_session: Session) -> Identity:
    """Create a test user."""
    user = Identity(id=1, name="test_user")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_group(db_session: Session) -> Group:
    """Create a test group."""
    group = Group(id="test-group", name="Test Group")
    db_session.add(group)
    db_session.commit()
    return group


class TestDirectoryRepository:
    """Unit tests for DirectoryRepository."""

    def test_save_and_get_directory(
        self, directory_repo: DirectoryRepository, test_user: Identity, db_session: Session
    ) -> None:
        """
        Test saving and retrieving a directory.
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Test Directory",
            parent_id=None,
            owner_id=test_user.id,
        )

        # Save
        saved = directory_repo.save(directory)
        assert saved.id == directory.id
        assert saved.name == "Test Directory"

        # Retrieve
        retrieved = directory_repo.get(directory.id)
        assert retrieved is not None
        assert retrieved.id == directory.id
        assert retrieved.name == "Test Directory"
        assert retrieved.owner_id == test_user.id

    def test_get_all_directories(
        self, directory_repo: DirectoryRepository, test_user: Identity, db_session: Session
    ) -> None:
        """
        Test retrieving all directories.
        """
        # Create multiple directories
        for i in range(3):
            directory = Directory(
                id=str(uuid.uuid4()),
                name=f"Directory {i}",
                parent_id=None,
                owner_id=test_user.id,
            )
            directory_repo.save(directory)

        # Get all
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])
        directories = directory_repo.get_all(access_permissions)
        assert len(directories) >= 3

    def test_delete_directory(
        self, directory_repo: DirectoryRepository, test_user: Identity, db_session: Session
    ) -> None:
        """
        Test deleting a directory.
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="To Delete",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(directory)

        # Verify exists
        assert directory_repo.get(directory.id) is not None

        # Delete
        directory_repo.delete(directory.id)

        # Verify deleted
        assert directory_repo.get(directory.id) is None

    def test_has_permission_owner(
        self, directory_repo: DirectoryRepository, test_user: Identity, db_session: Session
    ) -> None:
        """
        Test that owner has permission to access directory.
        """
        # Create directory owned by test_user
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Owner Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(directory)

        # Check permission as owner
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])
        assert directory_repo.has_permission(directory, access_permissions)

    def test_has_permission_group_member(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        test_group: Group,
        db_session: Session,
    ) -> None:
        """
        Test that group member has permission to access directory.
        """
        # Create another user as owner
        owner = Identity(id=2, name="owner_user")
        db_session.add(owner)
        db_session.commit()

        # Create directory with group
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Group Directory",
            parent_id=None,
            owner_id=owner.id,
        )
        directory.groups = [test_group]
        directory_repo.save(directory)

        # Check permission as group member (not owner)
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[test_group.id])
        assert directory_repo.has_permission(directory, access_permissions)

    def test_has_permission_no_access(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test that user without ownership or group membership has no permission.
        """
        # Create another user as owner
        owner = Identity(id=2, name="owner_user")
        db_session.add(owner)
        db_session.commit()

        # Create directory without test_user
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Private Directory",
            parent_id=None,
            owner_id=owner.id,
        )
        directory_repo.save(directory)

        # Check permission as non-owner, non-member
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[])
        assert not directory_repo.has_permission(directory, access_permissions)

    def test_has_permission_admin(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test that admin has permission to access any directory.
        """
        # Create another user as owner
        owner = Identity(id=2, name="owner_user")
        db_session.add(owner)
        db_session.commit()

        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Any Directory",
            parent_id=None,
            owner_id=owner.id,
        )
        directory_repo.save(directory)

        # Check permission as admin
        access_permissions = AccessPermissions(user_id=test_user.id, user_groups=[], is_admin=True)
        assert directory_repo.has_permission(directory, access_permissions)

    def test_check_cycle_self(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test that a directory cannot be its own parent (cycle detection).
        """
        directory_id = str(uuid.uuid4())
        assert directory_repo.check_cycle(directory_id, directory_id)

    def test_check_cycle_simple(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test cycle detection in simple hierarchy: A -> B, trying B -> A.
        """
        # Create A
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_a)

        # Create B with A as parent
        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=dir_a.id,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_b)

        # Try to make A a child of B (would create cycle)
        assert directory_repo.check_cycle(dir_a.id, dir_b.id)

    def test_check_cycle_deep(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test cycle detection in deep hierarchy: A -> B -> C, trying C -> A.
        """
        # Create A -> B -> C
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_a)

        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=dir_a.id,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_b)

        dir_c = Directory(
            id=str(uuid.uuid4()),
            name="C",
            parent_id=dir_b.id,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_c)

        # Try to make A a child of C (would create cycle)
        assert directory_repo.check_cycle(dir_a.id, dir_c.id)

    def test_check_cycle_no_cycle(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test that valid moves don't trigger cycle detection.
        """
        # Create A and B (siblings)
        dir_a = Directory(
            id=str(uuid.uuid4()),
            name="A",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_a)

        dir_b = Directory(
            id=str(uuid.uuid4()),
            name="B",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_b)

        # Create C under A
        dir_c = Directory(
            id=str(uuid.uuid4()),
            name="C",
            parent_id=dir_a.id,
            owner_id=test_user.id,
        )
        directory_repo.save(dir_c)

        # Move C under B (no cycle)
        assert not directory_repo.check_cycle(dir_c.id, dir_b.id)

    def test_has_duplicate_name_same_parent(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test duplicate name detection in same parent.
        """
        # Create parent
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(parent)

        # Create child
        child = Directory(
            id=str(uuid.uuid4()),
            name="Child",
            parent_id=parent.id,
            owner_id=test_user.id,
        )
        directory_repo.save(child)

        # Check for duplicate (should be true)
        assert directory_repo.has_duplicate_name("Child", parent.id)

    def test_has_duplicate_name_different_parent(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test that same name is allowed in different parents.
        """
        # Create two parents
        parent1 = Directory(
            id=str(uuid.uuid4()),
            name="Parent1",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(parent1)

        parent2 = Directory(
            id=str(uuid.uuid4()),
            name="Parent2",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(parent2)

        # Create child in parent1
        child = Directory(
            id=str(uuid.uuid4()),
            name="SameName",
            parent_id=parent1.id,
            owner_id=test_user.id,
        )
        directory_repo.save(child)

        # Check for duplicate in parent2 (should be false)
        assert not directory_repo.has_duplicate_name("SameName", parent2.id)

    def test_has_duplicate_name_with_exclude(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test duplicate name detection with exclusion (for updates).
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="ExistingName",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(directory)

        # Check duplicate excluding itself (should be false - allows rename to same name)
        assert not directory_repo.has_duplicate_name("ExistingName", None, exclude_id=directory.id)

    def test_has_children_directories(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test checking if directory has children.
        """
        # Create parent
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(parent)

        # Initially no children
        assert not directory_repo.has_children_directories(parent.id)

        # Create child
        child = Directory(
            id=str(uuid.uuid4()),
            name="Child",
            parent_id=parent.id,
            owner_id=test_user.id,
        )
        directory_repo.save(child)

        # Now has children
        assert directory_repo.has_children_directories(parent.id)

    def test_count_studies(
        self,
        directory_repo: DirectoryRepository,
        test_user: Identity,
        db_session: Session,
    ) -> None:
        """
        Test counting studies in a directory.
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Study Directory",
            parent_id=None,
            owner_id=test_user.id,
        )
        directory_repo.save(directory)

        # Count studies (should be 0 initially)
        count = directory_repo.count_studies(directory.id)
        assert count == 0

        # Note: To test with actual studies, we would need to create Study objects
        # which requires more complex setup. This is covered in integration tests.
