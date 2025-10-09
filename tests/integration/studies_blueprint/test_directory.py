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
Integration tests for directory management API endpoints.

These tests verify the complete flow of directory operations including:
- Creating, reading, updating, and deleting directories
- Permission checks and access control
- Hierarchical directory structure
- Study organization within directories
"""

from starlette.testclient import TestClient


class TestDirectoryManagement:
    """
    Integration tests for directory management endpoints.
    """

    def test_create_and_list_directories(self, client: TestClient, user_access_token: str) -> None:
        """
        Test creating directories and listing them.

        Scenario:
        1. Create a root directory
        2. Create a subdirectory
        3. List all directories
        4. Verify the hierarchy
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create root directory
        res = client.post(
            "/v1/directories",
            json={"name": "Project Alpha"},
        )
        assert res.status_code == 201, res.json()
        root_dir = res.json()
        assert root_dir["name"] == "Project Alpha"
        assert root_dir["parentId"] is None
        root_dir_id = root_dir["id"]

        # Create subdirectory
        res = client.post(
            "/v1/directories",
            json={"name": "Scenarios", "parentId": root_dir_id},
        )
        assert res.status_code == 201, res.json()
        sub_dir = res.json()
        assert sub_dir["name"] == "Scenarios"
        assert sub_dir["parentId"] == root_dir_id

        # List all directories
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        assert len(directories) >= 2
        dir_ids = [d["id"] for d in directories]
        assert root_dir_id in dir_ids
        assert sub_dir["id"] in dir_ids

    def test_get_directory_details(self, client: TestClient, user_access_token: str) -> None:
        """
        Test getting directory details by ID.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create directory
        res = client.post(
            "/v1/directories",
            json={"name": "Test Directory"},
        )
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Get directory details
        res = client.get(f"/v1/directories/{directory_id}")
        assert res.status_code == 200
        directory = res.json()
        assert directory["id"] == directory_id
        assert directory["name"] == "Test Directory"
        assert "owner" in directory
        assert "groups" in directory
        assert "createdAt" in directory
        assert "updatedAt" in directory

    def test_update_directory_name(self, client: TestClient, user_access_token: str) -> None:
        """
        Test updating a directory's name.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create directory
        res = client.post(
            "/v1/directories",
            json={"name": "Original Name"},
        )
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Update name
        res = client.put(
            f"/v1/directories/{directory_id}",
            json={"name": "Updated Name"},
        )
        assert res.status_code == 200
        updated_dir = res.json()
        assert updated_dir["name"] == "Updated Name"

        # Verify update
        res = client.get(f"/v1/directories/{directory_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "Updated Name"

    def test_move_directory_to_new_parent(self, client: TestClient, user_access_token: str) -> None:
        """
        Test moving a directory to a new parent.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create parent directories
        res = client.post("/v1/directories", json={"name": "Parent A"})
        assert res.status_code == 201
        parent_a_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "Parent B"})
        assert res.status_code == 201
        parent_b_id = res.json()["id"]

        # Create child under Parent A
        res = client.post(
            "/v1/directories",
            json={"name": "Child", "parentId": parent_a_id},
        )
        assert res.status_code == 201
        child_id = res.json()["id"]
        assert res.json()["parentId"] == parent_a_id

        # Move child to Parent B
        res = client.put(
            f"/v1/directories/{child_id}",
            json={"parentId": parent_b_id},
        )
        assert res.status_code == 200
        assert res.json()["parentId"] == parent_b_id

    def test_delete_empty_directory(self, client: TestClient, user_access_token: str) -> None:
        """
        Test deleting an empty directory (default mode).
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create directory
        res = client.post("/v1/directories", json={"name": "To Delete"})
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Delete directory
        res = client.delete(f"/v1/directories/{directory_id}")
        assert res.status_code == 204

        # Verify deletion
        res = client.get(f"/v1/directories/{directory_id}")
        assert res.status_code == 404

    def test_delete_non_empty_directory_fails(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that deleting a non-empty directory fails in default mode.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create parent directory
        res = client.post("/v1/directories", json={"name": "Parent"})
        assert res.status_code == 201
        parent_id = res.json()["id"]

        # Create child directory
        res = client.post(
            "/v1/directories",
            json={"name": "Child", "parentId": parent_id},
        )
        assert res.status_code == 201

        # Try to delete parent (should fail)
        res = client.delete(f"/v1/directories/{parent_id}")
        assert res.status_code == 409
        error_response = res.json()
        # Check if error message contains "subdirectories" in either detail or description
        error_msg = error_response.get("detail") or error_response.get("description", "")
        assert "subdirectories" in str(error_msg).lower()

    def test_delete_directory_with_force_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test deleting a directory with force mode (orphans subdirectories).
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create parent directory
        res = client.post("/v1/directories", json={"name": "Parent"})
        assert res.status_code == 201
        parent_id = res.json()["id"]

        # Create child directory
        res = client.post(
            "/v1/directories",
            json={"name": "Child", "parentId": parent_id},
        )
        assert res.status_code == 201
        child_id = res.json()["id"]

        # Delete parent with force=true
        res = client.delete(f"/v1/directories/{parent_id}?force=true")
        assert res.status_code == 204

        # Verify parent is deleted
        res = client.get(f"/v1/directories/{parent_id}")
        assert res.status_code == 404

        # Verify child still exists but is now at root (parent_id = null)
        res = client.get(f"/v1/directories/{child_id}")
        assert res.status_code == 200
        assert res.json()["parentId"] is None

    def test_prevent_directory_cycle(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that moving a directory cannot create a cycle.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create hierarchy: A -> B -> C
        res = client.post("/v1/directories", json={"name": "A"})
        assert res.status_code == 201
        dir_a_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "B", "parentId": dir_a_id})
        assert res.status_code == 201
        dir_b_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "C", "parentId": dir_b_id})
        assert res.status_code == 201
        dir_c_id = res.json()["id"]

        # Try to move A under C (would create cycle: C -> A -> B -> C)
        res = client.put(f"/v1/directories/{dir_a_id}", json={"parentId": dir_c_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

        # Try to move A under B (would create cycle: B -> A -> B)
        res = client.put(f"/v1/directories/{dir_a_id}", json={"parentId": dir_b_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

        # Try to move A under itself (should fail)
        res = client.put(f"/v1/directories/{dir_a_id}", json={"parentId": dir_a_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

    def test_duplicate_directory_name_in_same_parent(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that duplicate directory names are not allowed in the same parent.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create directory
        res = client.post("/v1/directories", json={"name": "Duplicate"})
        assert res.status_code == 201

        # Try to create another directory with same name at root
        res = client.post("/v1/directories", json={"name": "Duplicate"})
        assert res.status_code == 409
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "already exists" in str(error_msg).lower()

    def test_same_name_allowed_in_different_parents(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that the same directory name is allowed in different parents.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create two parent directories
        res = client.post("/v1/directories", json={"name": "Parent1"})
        assert res.status_code == 201
        parent1_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "Parent2"})
        assert res.status_code == 201
        parent2_id = res.json()["id"]

        # Create subdirectories with same name in different parents
        res = client.post(
            "/v1/directories",
            json={"name": "SameName", "parentId": parent1_id},
        )
        assert res.status_code == 201

        res = client.post(
            "/v1/directories",
            json={"name": "SameName", "parentId": parent2_id},
        )
        assert res.status_code == 201

    def test_list_studies_in_directory(self, client: TestClient, user_access_token: str) -> None:
        """
        Test listing studies in a directory.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create directory
        res = client.post("/v1/directories", json={"name": "Study Container"})
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Create a study
        res = client.post("/v1/studies?name=test-study&version=8.8")
        assert res.status_code == 201
        # Note: Moving a study to a directory requires updating study.directory_id
        # This would be done via PATCH /v1/studies/{study_id}
        # For now, we just test that the endpoint works (returns empty list)

        # List studies in directory
        res = client.get(f"/v1/directories/{directory_id}/studies")
        assert res.status_code == 200
        studies = res.json()
        assert isinstance(studies, list)

    def test_directory_not_found(self, client: TestClient, user_access_token: str) -> None:
        """
        Test accessing a non-existent directory returns 404.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        fake_id = "00000000-0000-0000-0000-000000000000"
        res = client.get(f"/v1/directories/{fake_id}")
        assert res.status_code == 404

    def test_invalid_directory_name(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that invalid directory names are rejected.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Empty name
        res = client.post("/v1/directories", json={"name": ""})
        assert res.status_code == 422

        # Name with path separators
        res = client.post("/v1/directories", json={"name": "invalid/name"})
        assert res.status_code == 422

        res = client.post("/v1/directories", json={"name": "invalid\\name"})
        assert res.status_code == 422

    def test_deep_directory_hierarchy(self, client: TestClient, user_access_token: str) -> None:
        """
        Test creating a deep directory hierarchy (no depth limit as per user requirement).
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        parent_id = None
        depth = 15  # Create 15 levels to verify no limit

        for i in range(depth):
            json_data = {"name": f"Level{i}"}
            if parent_id:
                json_data["parentId"] = parent_id

            res = client.post("/v1/directories", json=json_data)
            assert res.status_code == 201, f"Failed at depth {i}"
            parent_id = res.json()["id"]

        # Verify the deepest directory exists
        res = client.get(f"/v1/directories/{parent_id}")
        assert res.status_code == 200
        assert res.json()["name"] == f"Level{depth - 1}"
