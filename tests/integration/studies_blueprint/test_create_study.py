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


class TestCreateStudy:
    def test_create_study_with_different_names(
        self,
        client: TestClient,
        admin_access_token: str,
    ) -> None:
        res = client.post("/v1/studies?name=study1", headers={"Authorization": f"Bearer {admin_access_token}"})
        assert res.status_code == 201

        id = client.post("/v1/studies?name=study2  ", headers={"Authorization": f"Bearer {admin_access_token}"}).json()
        res = client.get("/v1/studies?name=study2", headers={"Authorization": f"Bearer {admin_access_token}"})
        assert res.status_code == 200
        assert res.json()[id]["name"] == "study2"

        res = client.post("/v1/studies?name=study3=", headers={"Authorization": f"Bearer {admin_access_token}"})
        assert res.status_code == 400
        assert res.json() == {
            "description": "study name study3= contains illegal characters (=, /)",
            "exception": "HTTPException",
        }

        res = client.post("/v1/studies?name=stu / dy4", headers={"Authorization": f"Bearer {admin_access_token}"})
        assert res.status_code == 400
        assert res.json() == {
            "description": "study name stu / dy4 contains illegal characters (=, /)",
            "exception": "HTTPException",
        }
