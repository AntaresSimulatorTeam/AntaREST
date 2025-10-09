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

from starlette.testclient import TestClient


class TestMove:
    def test_move_endpoint(self, client: TestClient, internal_study_id: str, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        res = client.post("/v1/studies?name=study_test")
        assert res.status_code == 201
        study_id = res.json()

        # Create directories first (required since move now validates directory existence)
        res = client.post("/v1/directories", json={"name": "folder1"})
        assert res.status_code == 201

        res = client.post("/v1/directories", json={"name": "folder2"})
        assert res.status_code == 201

        # asserts move with a given folder adds the /study_id at the end of the path
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "folder1"})
        res.raise_for_status()
        res = client.get(f"/v1/studies/{study_id}")
        assert res.json()["folder"] == f"folder1/{study_id}"

        # asserts move to a folder with //// removes the unwanted `/`
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "folder2///////"})
        res.raise_for_status()
        res = client.get(f"/v1/studies/{study_id}")
        assert res.json()["folder"] == f"folder2/{study_id}"

        # asserts the created variant has the same parent folder
        res = client.post(f"/v1/studies/{study_id}/variants?name=Variant1")
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}")
        assert res.json()["folder"] == f"folder2/{variant_id}"

        # asserts move doesn't work on un-managed studies
        res = client.put(f"/v1/studies/{internal_study_id}/move", params={"folder_dest": "folder1"})
        assert res.status_code == 422
        assert res.json()["exception"] == "NotAManagedStudyException"

        # asserts users can put back a study at the root folder
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": ""})
        res.raise_for_status()
        res = client.get(f"/v1/studies/{study_id}")
        assert res.json()["folder"] is None

    def test_move_with_directory_validation(self, client: TestClient, user_access_token: str) -> None:
        """Test that move validates directory existence."""
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a study
        res = client.post("/v1/studies?name=study_move")
        assert res.status_code == 201
        study_id = res.json()

        # Try to move to non-existent directory - should fail
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "nonexistent/folder"})
        assert res.status_code == 404
        error = res.json()
        error_msg = error.get("detail") or error.get("description", "")
        assert "does not exist" in error_msg.lower()

        # Create directory structure
        res = client.post("/v1/directories", json={"name": "project"})
        assert res.status_code == 201
        project_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "folder", "parentId": project_id})
        assert res.status_code == 201

        # Now move should succeed
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "project/folder"})
        assert res.status_code == 200

        # Verify the study moved
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["folder"] == f"project/folder/{study_id}"
