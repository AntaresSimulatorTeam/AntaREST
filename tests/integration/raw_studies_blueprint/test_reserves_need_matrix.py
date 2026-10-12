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

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


class TestReserveNeedMatrix:
    @pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
    def test_crud_on_reserve_need_matrix_via_raw(
        self, client: TestClient, user_access_token: str, storage_mode: str
    ) -> None:
        preparer = PreparerProxy(client, user_access_token)

        study_id = preparer.create_study("reserve-need-test", version=1020, storage_mode=storage_mode)

        preparer.create_area(study_id, name="fr")

        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"name": "R1", "type": "up"},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        reserve = res.json()
        reserve_id = reserve["id"]
        assert reserve_id == "r1"
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

        # Download with the default headers: reserve needs have one time-series column.
        res = client.get(
            f"/v1/studies/{study_id}/raw/download",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.text
        downloaded = pd.read_csv(io.BytesIO(res.content), index_col=0)
        assert list(downloaded.columns) == ["TS-1"]
        assert downloaded.shape == (8760, 1)
        np.testing.assert_allclose(downloaded.to_numpy(), np.asarray(custom_values))

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
