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
import pytest
from antares.study.version import StudyVersion
from starlette.testclient import TestClient


class TestCreateStudy:
    @pytest.mark.parametrize(
        "study_version",
        [
            "7.0",
            "7.1",
            "7.2",
            "8.0",
            "8.1",
            "8.2",
            "8.3",
            "8.4",
            "8.5",
            "8.6",
            "8.7",
            "8.7",
            "9.2",
            "9.3",
        ],
    )
    def test_create_study_versions(
        self,
        study_version: str,
        client: TestClient,
        admin_access_token: str,
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post(f"/v1/studies?name=study&version={study_version}")
        assert res.status_code == 201
        study_id = res.json()

        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        study_metadata = res.json()
        assert study_metadata["name"] == "study"
        assert StudyVersion.parse(study_metadata["version"]) == StudyVersion.parse(study_version)

    def test_create_study_with_different_names(
        self,
        client: TestClient,
        admin_access_token: str,
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post("/v1/studies?name=study1")
        assert res.status_code == 201

        id = client.post("/v1/studies?name=study2  ").json()
        res = client.get("/v1/studies?name=study2")
        assert res.status_code == 200
        assert res.json()[id]["name"] == "study2"

        res = client.post("/v1/studies?name=study3=")
        assert res.status_code == 400
        assert res.json() == {
            "description": "study name study3= contains illegal characters (=, /)",
            "exception": "HTTPException",
        }

        res = client.post("/v1/studies?name=stu / dy4")
        assert res.status_code == 400
        assert res.json() == {
            "description": "study name stu / dy4 contains illegal characters (=, /)",
            "exception": "HTTPException",
        }

    def test_create_study_with_path(
        self,
        client: TestClient,
        admin_access_token: str,
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        # First create the directory structure
        res = client.post("/v1/directories", json={"name": "project"})
        assert res.status_code == 201
        project_dir_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "subfolder", "parentId": project_dir_id})
        assert res.status_code == 201

        # Create study in the directory path
        res = client.post("/v1/studies?name=test-study&directory=project/subfolder")
        assert res.status_code == 201
        study_id = res.json()

        # Verify the study has the correct directory_id
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        study = res.json()
        assert study["name"] == "test-study"

    def test_create_study_with_auto_directory_creation(
        self,
        client: TestClient,
        admin_access_token: str,
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post("/v1/studies?name=test-study&directory=workspace/experiments/test")
        assert res.status_code == 201
        study_id = res.json()

        # Verify the study was created
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "test-study"

        # Verify directories were created
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_names = [d["name"] for d in directories]
        assert "workspace" in dir_names
        assert "experiments" in dir_names
        assert "test" in dir_names

        # Verify hierarchy
        workspace_dir = next(d for d in directories if d["name"] == "workspace")
        assert workspace_dir["parentId"] is None

        experiments_dir = next(d for d in directories if d["name"] == "experiments")
        assert experiments_dir["parentId"] == workspace_dir["id"]

        test_dir = next(d for d in directories if d["name"] == "test")
        assert test_dir["parentId"] == experiments_dir["id"]
