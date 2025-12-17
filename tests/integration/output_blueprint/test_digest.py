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


class TestDigest:
    def test_get_digest_endpoint(self, client: TestClient, user_access_token: str, internal_study_id: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Nominal case
        output_id = "20201014-1422eco-hello"
        res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{output_id}/digest-ui")
        assert res.status_code == 200
        digest = res.json()
        assert list(digest.keys()) == ["area", "districts", "flowLinear", "flowQuadratic"]
        assert digest["districts"] == {"columns": [], "data": [], "groupedColumns": False}
        flow = {
            "columns": ["", "de", "es", "fr", "it"],
            "data": [
                ["de", "X", "--", "0", "--"],
                ["es", "--", "X", "0", "--"],
                ["fr", "0", "0", "X", "0"],
                ["it", "--", "--", "0", "X"],
            ],
            "groupedColumns": False,
        }
        assert digest["flowQuadratic"] == flow
        assert digest["flowLinear"] == flow
        area_matrix = digest["area"]
        assert area_matrix["groupedColumns"] is True
        assert area_matrix["columns"][:3] == [[""], ["OV. COST", "Euro", "EXP"], ["OP. COST", "Euro", "EXP"]]

        # Asserts we have a 404 Exception when the output doesn't exist
        fake_output = "fake_output"
        res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{fake_output}/digest-ui")
        assert res.status_code == 404
        assert res.json() == {
            "description": f"'{fake_output}' not a child of Output",
            "exception": "ChildNotFoundError",
        }

        # Asserts we have a 404 Exception when the digest file doesn't exist
        output_wo_digest = "20201014-1430adq"
        res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{output_wo_digest}/digest-ui")
        assert res.status_code == 404
        assert res.json() == {
            "description": "'economy' not a child of OutputSimulation",
            "exception": "ChildNotFoundError",
        }
