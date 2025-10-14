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

import io
import zipfile

from starlette.testclient import TestClient


class TestStudyWithDirectories:
    def test_copy_study_with_path(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create source study
        res = client.post("/v1/studies?name=source-study")
        assert res.status_code == 201
        source_study_id = res.json()

        # Create directory structure
        res = client.post("/v1/directories", json={"name": "backup"})
        assert res.status_code == 201
        backup_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "2025", "parentId": backup_id})
        assert res.status_code == 201

        # Copy study to directory path
        res = client.post(
            f"/v1/studies/{source_study_id}/copy",
            params={"study_name": "copied-study", "use_task": False, "path": "backup/2025"},
        )
        assert res.status_code == 201
        copied_study_id = res.json()

        # Verify copied study exists
        res = client.get(f"/v1/studies/{copied_study_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "copied-study"

    def test_copy_study_with_auto_directory_creation(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create source study
        res = client.post("/v1/studies?name=source-study")
        assert res.status_code == 201
        source_study_id = res.json()

        # Copy to non-existent path - should succeed and create directories
        res = client.post(
            f"/v1/studies/{source_study_id}/copy",
            params={"study_name": "copied-study", "use_task": False, "path": "archives/projects/2025"},
        )
        assert res.status_code == 201
        copied_study_id = res.json()

        # Verify copied study exists
        res = client.get(f"/v1/studies/{copied_study_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "copied-study"

        # Verify directories were created
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_names = [d["name"] for d in directories]
        assert "archives" in dir_names
        assert "projects" in dir_names
        assert "2025" in dir_names

        # Verify hierarchy
        archives_dir = next(d for d in directories if d["name"] == "archives")
        assert archives_dir["parentId"] is None

        projects_dir = next(d for d in directories if d["name"] == "projects")
        assert projects_dir["parentId"] == archives_dir["id"]

        year_dir = next(d for d in directories if d["name"] == "2025")
        assert year_dir["parentId"] == projects_dir["id"]

    def test_copy_study_without_path(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create source study
        res = client.post("/v1/studies?name=source-study")
        assert res.status_code == 201
        source_study_id = res.json()

        # Copy without path
        res = client.post(
            f"/v1/studies/{source_study_id}/copy",
            params={"study_name": "copied-study", "use_task": False},
        )
        assert res.status_code == 201
        copied_study_id = res.json()

        # Verify copied study exists
        res = client.get(f"/v1/studies/{copied_study_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "copied-study"

    def test_import_study_with_path(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a simple zip file (minimal study structure)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # Minimal study.antares file
            zf.writestr("study.antares", "[antares]\nversion = 900\ncaption = Test Study\n")

        zip_buffer.seek(0)

        # Create directory structure
        res = client.post("/v1/directories", json={"name": "imports"})
        assert res.status_code == 201
        imports_id = res.json()["id"]

        res = client.post("/v1/directories", json={"name": "external", "parentId": imports_id})
        assert res.status_code == 201

        # Import study to directory path
        res = client.post(
            "/v1/studies/_import",
            params={"path": "imports/external"},
            files={"study": ("study.zip", zip_buffer, "application/zip")},
        )
        assert res.status_code == 201
        study_id = res.json()

        # Verify imported study exists
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200

    def test_import_study_with_auto_directory_creation(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a simple zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("study.antares", "[antares]\nversion = 900\ncaption = Test Study\n")

        zip_buffer.seek(0)

        # Import to non-existent path - should succeed and create directories
        res = client.post(
            "/v1/studies/_import",
            params={"path": "uploads/incoming/batch1"},
            files={"study": ("study.zip", zip_buffer, "application/zip")},
        )
        assert res.status_code == 201
        study_id = res.json()

        # Verify imported study exists
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200

        # Verify directories were created
        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_names = [d["name"] for d in directories]
        assert "uploads" in dir_names
        assert "incoming" in dir_names
        assert "batch1" in dir_names

        # Verify hierarchy
        uploads_dir = next(d for d in directories if d["name"] == "uploads")
        assert uploads_dir["parentId"] is None

        incoming_dir = next(d for d in directories if d["name"] == "incoming")
        assert incoming_dir["parentId"] == uploads_dir["id"]

        batch_dir = next(d for d in directories if d["name"] == "batch1")
        assert batch_dir["parentId"] == incoming_dir["id"]
