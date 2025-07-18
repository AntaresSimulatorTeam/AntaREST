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

        # asserts move with a given folder adds the /study_id at the end of the path
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "folder1"})
        res.raise_for_status()
        res = client.get(f"/v1/studies/{study_id}")
        assert res.json()["folder"] == f"folder1/{study_id}"

        # asserts move to a folder with //// removes the unwanted `/`
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": "folder2///////"})
        assert res.status_code == 400
        assert res.json() == {
            "description": "folder name folder2/////// cannot end with '/'",
            "exception": "HTTPException",
        }

        # asserts the created variant has the same parent folder
        res = client.post(f"/v1/studies/{study_id}/variants?name=Variant1")
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}")
        assert res.json()["folder"] == f"folder1/{variant_id}"

        # asserts move doesn't work on un-managed studies
        res = client.put(f"/v1/studies/{internal_study_id}/move", params={"folder_dest": "folder1"})
        assert res.status_code == 422
        assert res.json()["exception"] == "NotAManagedStudyException"

        # asserts users can put back a study at the root folder
        res = client.put(f"/v1/studies/{study_id}/move", params={"folder_dest": ""})
        res.raise_for_status()
        res = client.get(f"/v1/studies/{study_id}")
        assert res.json()["folder"] is None
