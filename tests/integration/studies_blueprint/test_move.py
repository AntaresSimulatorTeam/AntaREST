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

from httpx import Headers
from starlette.testclient import TestClient


class TestMove:
    def test_move_endpoint(self, client: TestClient, internal_study_id: str, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        res = client.post("/v1/studies?name=study_test")
        assert res.status_code == 201
        study_id = res.json()

        # Move creates directories automatically if they don't exist
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

    def test_move_with_auto_directory_creation(self, client: TestClient, user_access_token: str) -> None:
        """Test that move creates missing directories automatically."""
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        # Create a study
        res = client.post("/v1/studies?name=study_move")
        assert res.status_code == 201
        study_id = res.json()

        # Move to non-existent directory - should succeed and create directories
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "project/subfolder/deep"})
        assert res.status_code == 200

        # Verify the study moved
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["folder"] == f"project/subfolder/deep/{study_id}"

        # Verify directories were created
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_names = [d["name"] for d in directories]
        assert "project" in dir_names
        assert "subfolder" in dir_names
        assert "deep" in dir_names

        # Verify hierarchy
        project_dir = next(d for d in directories if d["name"] == "project")
        assert project_dir["parentId"] is None

        subfolder_dir = next(d for d in directories if d["name"] == "subfolder")
        assert subfolder_dir["parentId"] == project_dir["id"]

        deep_dir = next(d for d in directories if d["name"] == "deep")
        assert deep_dir["parentId"] == subfolder_dir["id"]
