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

import pytest
from sqlalchemy.orm import Session

from antarest.login.model import Identity
from antarest.study.model import Directory
from antarest.study.repository import DirectoryRepository
from tests.helpers import create_raw_study


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

    def test_exists_by_id(self, directory_repo: DirectoryRepository, db_session: Session, test_user: Identity) -> None:
        """
        Test checking if directory exists by ID.
        """
        # Create directory
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Test Directory",
            parent_id=None,
        )
        directory_repo.save(directory)

        # Should exist
        assert directory_repo.exists_by_id(directory.id)

        # Should not exist for random ID
        assert not directory_repo.exists_by_id(str(uuid.uuid4()))

        # Delete and verify it no longer exists
        directory_repo.delete(directory.id)
        assert not directory_repo.exists_by_id(directory.id)

    def test_count_studies_in_tree(
        self, directory_repo: DirectoryRepository, db_session: Session, test_user: Identity
    ) -> None:
        """
        Test counting studies in a directory tree (including subdirectories).
        """
        # Create directory hierarchy: parent -> child1, child2 -> grandchild
        parent = Directory(
            id=str(uuid.uuid4()),
            name="Parent",
            parent_id=None,
        )
        directory_repo.save(parent)

        child1 = Directory(
            id=str(uuid.uuid4()),
            name="Child1",
            parent_id=parent.id,
        )
        directory_repo.save(child1)

        child2 = Directory(
            id=str(uuid.uuid4()),
            name="Child2",
            parent_id=parent.id,
        )
        directory_repo.save(child2)

        grandchild = Directory(
            id=str(uuid.uuid4()),
            name="Grandchild",
            parent_id=child2.id,
        )
        directory_repo.save(grandchild)

        # Initially no studies
        assert directory_repo.count_studies_in_tree(parent.id) == 0

        # Add study to parent
        study1 = create_raw_study(id=str(uuid.uuid4()), name="Study1", directory_id=parent.id, owner=test_user)
        db_session.add(study1)
        db_session.commit()

        # Should count 1 study
        assert directory_repo.count_studies_in_tree(parent.id) == 1

        # Add study to child1
        study2 = create_raw_study(id=str(uuid.uuid4()), name="Study2", directory_id=child1.id, owner=test_user)
        db_session.add(study2)
        db_session.commit()

        # Should count 2 studies (parent + child1)
        assert directory_repo.count_studies_in_tree(parent.id) == 2

        # Add study to grandchild
        study3 = create_raw_study(id=str(uuid.uuid4()), name="Study3", directory_id=grandchild.id, owner=test_user)
        db_session.add(study3)
        db_session.commit()

        # Should count 3 studies (parent + child1 + grandchild)
        assert directory_repo.count_studies_in_tree(parent.id) == 3

        # Count from child2 should only include grandchild
        assert directory_repo.count_studies_in_tree(child2.id) == 1

        # Count from child1 should only include itself
        assert directory_repo.count_studies_in_tree(child1.id) == 1

    def test_count_studies_in_tree_empty(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test counting studies in an empty directory tree.
        """
        # Create directory with no children and no studies
        directory = Directory(
            id=str(uuid.uuid4()),
            name="Empty Directory",
            parent_id=None,
        )
        directory_repo.save(directory)

        # Should count 0 studies
        assert directory_repo.count_studies_in_tree(directory.id) == 0

    def test_get_all_descendant_directories(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test getting all descendant directories using recursive CTE.
        """
        # Create directory hierarchy: root -> child1, child2 -> grandchild1, grandchild2
        root = Directory(
            id=str(uuid.uuid4()),
            name="Root",
            parent_id=None,
        )
        directory_repo.save(root)

        child1 = Directory(
            id=str(uuid.uuid4()),
            name="Child1",
            parent_id=root.id,
        )
        directory_repo.save(child1)

        child2 = Directory(
            id=str(uuid.uuid4()),
            name="Child2",
            parent_id=root.id,
        )
        directory_repo.save(child2)

        grandchild1 = Directory(
            id=str(uuid.uuid4()),
            name="Grandchild1",
            parent_id=child1.id,
        )
        directory_repo.save(grandchild1)

        grandchild2 = Directory(
            id=str(uuid.uuid4()),
            name="Grandchild2",
            parent_id=child2.id,
        )
        directory_repo.save(grandchild2)

        # Get all descendants from root
        descendants = directory_repo.get_all_descendant_directories(root.id)

        # Should include all 4 descendants
        descendant_ids = {d.id for d in descendants}
        assert len(descendant_ids) == 4
        assert child1.id in descendant_ids
        assert child2.id in descendant_ids
        assert grandchild1.id in descendant_ids
        assert grandchild2.id in descendant_ids

        # Get descendants from child1
        descendants_child1 = directory_repo.get_all_descendant_directories(child1.id)
        descendant_ids_child1 = {d.id for d in descendants_child1}
        assert len(descendant_ids_child1) == 1
        assert grandchild1.id in descendant_ids_child1

        # Get descendants from child2
        descendants_child2 = directory_repo.get_all_descendant_directories(child2.id)
        descendant_ids_child2 = {d.id for d in descendants_child2}
        assert len(descendant_ids_child2) == 1
        assert grandchild2.id in descendant_ids_child2

    def test_get_all_descendant_directories_empty(
        self, directory_repo: DirectoryRepository, test_user: Identity
    ) -> None:
        """
        Test getting descendants from a directory with no children.
        """
        # Create leaf directory
        leaf = Directory(
            id=str(uuid.uuid4()),
            name="Leaf",
            parent_id=None,
        )
        directory_repo.save(leaf)

        # Should return empty list
        descendants = directory_repo.get_all_descendant_directories(leaf.id)
        assert len(descendants) == 0

    def test_get_directory_paths_bulk(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test getting directory paths in bulk using recursive CTE.
        """
        # Create directory hierarchy: root -> child -> grandchild
        root = Directory(
            id=str(uuid.uuid4()),
            name="project",
            parent_id=None,
        )
        directory_repo.save(root)

        child = Directory(
            id=str(uuid.uuid4()),
            name="subfolder",
            parent_id=root.id,
        )
        directory_repo.save(child)

        grandchild = Directory(
            id=str(uuid.uuid4()),
            name="deep",
            parent_id=child.id,
        )
        directory_repo.save(grandchild)

        # Get paths for all directories
        paths = directory_repo.get_directory_paths_bulk([root.id, child.id, grandchild.id])

        # Verify paths
        assert paths[root.id] == "project"
        assert paths[child.id] == "project/subfolder"
        assert paths[grandchild.id] == "project/subfolder/deep"

    def test_get_directory_paths_bulk_multiple_roots(
        self, directory_repo: DirectoryRepository, test_user: Identity
    ) -> None:
        """
        Test getting directory paths for multiple root-level directories.
        """
        # Create two separate hierarchies
        root1 = Directory(
            id=str(uuid.uuid4()),
            name="project1",
            parent_id=None,
        )
        directory_repo.save(root1)

        child1 = Directory(
            id=str(uuid.uuid4()),
            name="src",
            parent_id=root1.id,
        )
        directory_repo.save(child1)

        root2 = Directory(
            id=str(uuid.uuid4()),
            name="project2",
            parent_id=None,
        )
        directory_repo.save(root2)

        child2 = Directory(
            id=str(uuid.uuid4()),
            name="lib",
            parent_id=root2.id,
        )
        directory_repo.save(child2)

        # Get paths for all directories
        paths = directory_repo.get_directory_paths_bulk([root1.id, child1.id, root2.id, child2.id])

        # Verify paths
        assert paths[root1.id] == "project1"
        assert paths[child1.id] == "project1/src"
        assert paths[root2.id] == "project2"
        assert paths[child2.id] == "project2/lib"

    def test_get_directory_paths_bulk_empty(self, directory_repo: DirectoryRepository, test_user: Identity) -> None:
        """
        Test getting directory paths with empty input.
        """
        # Should return empty dict
        paths = directory_repo.get_directory_paths_bulk([])
        assert paths == {}

    def test_get_directory_paths_bulk_nonexistent(
        self, directory_repo: DirectoryRepository, test_user: Identity
    ) -> None:
        """
        Test getting directory paths for non-existent directory IDs.
        """
        # Request paths for non-existent IDs
        fake_id = str(uuid.uuid4())
        paths = directory_repo.get_directory_paths_bulk([fake_id])

        # Should return empty dict (no matches)
        assert fake_id not in paths
