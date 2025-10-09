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
    """Test study operations (copy, import) with directory path parameter."""

    def test_copy_study_with_path(self, client: TestClient, user_access_token: str) -> None:
        """Test copying a study to a specific directory path."""
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

    def test_copy_study_with_nonexistent_path(self, client: TestClient, user_access_token: str) -> None:
        """Test copying a study to non-existent directory should fail."""
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create source study
        res = client.post("/v1/studies?name=source-study")
        assert res.status_code == 201
        source_study_id = res.json()

        # Try to copy to non-existent path
        res = client.post(
            f"/v1/studies/{source_study_id}/copy",
            params={"study_name": "copied-study", "use_task": False, "path": "nonexistent/path"},
        )
        assert res.status_code == 404
        error = res.json()
        error_msg = error.get("detail") or error.get("description", "")
        assert "does not exist" in error_msg.lower()

    def test_copy_study_without_path(self, client: TestClient, user_access_token: str) -> None:
        """Test copying a study without path creates it at root level."""
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
        """Test importing a study to a specific directory path."""
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

    def test_import_study_with_nonexistent_path(self, client: TestClient, user_access_token: str) -> None:
        """Test importing a study to non-existent directory should fail."""
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a simple zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("study.antares", "[antares]\nversion = 900\ncaption = Test Study\n")

        zip_buffer.seek(0)

        # Try to import to non-existent path
        res = client.post(
            "/v1/studies/_import",
            params={"path": "nonexistent/path"},
            files={"study": ("study.zip", zip_buffer, "application/zip")},
        )
        assert res.status_code == 404
        error = res.json()
        error_msg = error.get("detail") or error.get("description", "")
        assert "does not exist" in error_msg.lower()
