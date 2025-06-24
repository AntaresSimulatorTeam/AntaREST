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


def test_matrix(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    matrix = [[1, 2], [1, 7]]

    # Creating matrix and checking the metadata inside it
    res = client.post(
        "/v1/matrix",
        json=matrix,
    )

    matrix_id = res.json()

    res = client.get("/v1/matrix")
    assert res.status_code == 200
    matrices = res.json()

    existing_matrix = any(d.get("id") == matrix_id for d in matrices)
    assert existing_matrix

    res = client.get(f"/v1/matrix/{matrix_id}")
    actual_matrix = res.json()
    actual_width = actual_matrix["data"][0]
    actual_height = actual_matrix["data"][1]

    assert len(actual_width) == 2
    assert len(actual_height) == 2

