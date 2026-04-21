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
import io

from starlette.testclient import TestClient

from tests.integration.assets import ASSETS_DIR


class TestImportStudyDirectory:
    def test_import_without_directory_sets_no_directory_id(self, client: TestClient, admin_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")

        res = client.post("/v1/studies/_import", files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())})
        assert res.status_code == 201, res.json()
        study_id = res.json()

        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["directory_id"] is None

    def test_import_with_existing_directory_sets_directory_id(
        self, client: TestClient, admin_access_token: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")

        res = client.post("/v1/directories", json={"name": "imports"})
        assert res.status_code == 201, res.json()
        target_dir_id = res.json()["id"]

        res = client.post(
            "/v1/studies/_import?directory=imports",
            files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["directory_id"] == target_dir_id

    def test_import_with_nested_path_auto_creates_directories(
        self, client: TestClient, admin_access_token: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")

        res = client.post(
            "/v1/studies/_import?directory=project/experiments/runA",
            files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        res = client.get("/v1/directories")
        assert res.status_code == 200
        directories = res.json()
        dir_names = {d["name"] for d in directories}
        assert {"project", "experiments", "runA"}.issubset(dir_names)

        leaf_id = next(d["id"] for d in directories if d["name"] == "runA")
        res = client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200
        assert res.json()["directory_id"] == leaf_id

    def test_import_with_invalid_directory_is_rejected(self, client: TestClient, admin_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")

        res = client.post(
            "/v1/studies/_import?directory=bad=folder",
            files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())},
        )
        assert res.status_code == 400
        assert "illegal character" in res.json()["description"]
