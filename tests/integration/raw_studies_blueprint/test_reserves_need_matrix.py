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

import numpy as np
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


class TestReserveNeedMatrix:
    def test_crud_on_reserve_need_matrix_via_raw(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)

        study_id = preparer.create_study("reserve-need-test", version=1000, storage_mode="database")

        preparer.create_area(study_id, name="fr")

        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"id": "R1", "type": "up"},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        reserve = res.json()
        reserve_id = reserve["id"]
        assert reserve_id == "R1"
        assert reserve["type"] == "up"

        matrix_path = f"input/reserves/fr/{reserve_id}"

        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body = res.json()
        assert "data" in body
        assert "index" in body
        assert "columns" in body
        data = np.asarray(body["data"], dtype=float)
        assert data.shape == (8760, 1)
        assert data.sum() == 0.0

        custom_values = [[i * 0.1] for i in range(8760)]
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
            json=custom_values,
        )
        assert res.status_code == 200, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body = res.json()
        data = np.asarray(body["data"], dtype=float)
        assert data.shape == (8760, 1)
        np.testing.assert_allclose(data, np.asarray(custom_values))

        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json=[reserve_id],
            headers=preparer.headers,
        )
        assert res.status_code == 204, res.text

        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 404, res.json()
