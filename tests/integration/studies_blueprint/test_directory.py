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
from httpx import Headers
from starlette.testclient import TestClient


class TestDirectoryManagement:
    def test_create_and_list_directories(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Create root directory
        res = client.post(
            "/v1/directories",
            json={"name": "Antarest"},
        )
        assert res.status_code == 201, res.json()
        root_dir = res.json()
        assert root_dir["name"] == "Antarest"
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

    def test_update_directory_name(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Create directory
        res = client.post(
            "/v1/directories",
            json={"name": "Original Name"},
        )
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Update name
        res = client.patch(
            f"/v1/directories/{directory_id}",
            json={"name": "Updated Name"},
        )
        assert res.status_code == 200
        updated_dir = res.json()
        assert updated_dir["name"] == "Updated Name"

        # Verify update by listing all directories
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        updated_dir = next((d for d in directories if d["id"] == directory_id), None)
        assert updated_dir is not None
        assert updated_dir["name"] == "Updated Name"

    def test_move_directory_to_new_parent(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

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
        res = client.patch(
            f"/v1/directories/{child_id}",
            json={"parentId": parent_b_id},
        )
        assert res.status_code == 200
        assert res.json()["parentId"] == parent_b_id

    def test_delete_empty_directory(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Create directory
        res = client.post("/v1/directories", json={"name": "To Delete"})
        assert res.status_code == 201
        directory_id = res.json()["id"]

        # Delete directory
        res = client.delete(f"/v1/directories/{directory_id}")
        assert res.status_code == 204

        # Verify deletion by listing directories
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_ids = [d["id"] for d in directories]
        assert directory_id not in dir_ids

    def test_prevent_directory_cycle(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

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
        res = client.patch(f"/v1/directories/{dir_a_id}", json={"parentId": dir_c_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

        # Try to move A under B (would create cycle: B -> A -> B)
        res = client.patch(f"/v1/directories/{dir_a_id}", json={"parentId": dir_b_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

        # Try to move A under itself (should fail)
        res = client.patch(f"/v1/directories/{dir_a_id}", json={"parentId": dir_a_id})
        assert res.status_code == 400
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "cycle" in str(error_msg).lower()

    def test_duplicate_directory_name_in_same_parent(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Create directory
        res = client.post("/v1/directories", json={"name": "Duplicate"})
        assert res.status_code == 201

        # Try to create another directory with same name at root
        res = client.post("/v1/directories", json={"name": "Duplicate"})
        assert res.status_code == 409
        error_msg = res.json().get("detail") or res.json().get("description", "")
        assert "already exists" in str(error_msg).lower()

    def test_same_name_allowed_in_different_parents(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

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

    def test_invalid_directory_name(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Empty name
        res = client.post("/v1/directories", json={"name": ""})
        assert res.status_code == 422

        # Name with path separators
        res = client.post("/v1/directories", json={"name": "invalid/name"})
        assert res.status_code == 422

        res = client.post("/v1/directories", json={"name": "invalid\\name"})
        assert res.status_code == 422

    def test_deep_directory_hierarchy(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        parent_id = None
        depth = 15  # Create 15 levels to verify no limit

        for i in range(depth):
            json_data = {"name": f"Level{i}"}
            if parent_id:
                json_data["parentId"] = parent_id

            res = client.post("/v1/directories", json=json_data)
            assert res.status_code == 201, f"Failed at depth {i}"
            parent_id = res.json()["id"]

        # Verify all directories were created by listing them
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        level_dirs = [d for d in directories if d["name"].startswith("Level")]
        assert len(level_dirs) == depth
