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
from datetime import datetime

from starlette.testclient import TestClient


def test_get_matrices(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    matrix = [[1, 2], [1, 7]]
    matrix_1 = [[3, 6], [5, 10, 28]]
    time_format = "%Y-%m-%d %H:%M:%S.%f"

    # Creating matrix and checking the metadata inside it
    res = client.post(
        "/v1/matrix",
        json=matrix,
    )

    second_last_matrix_id = res.json()

    res = client.post(
        "/v1/matrix",
        json=matrix_1,
    )

    last_matrix_id = res.json()

    res = client.get("/v1/matrix")
    assert res.status_code == 200
    matrices = res.json()

    second_last_matrix = matrices[-2]
    is_date_format_ok = bool(datetime.strptime(second_last_matrix["created_at"], time_format))
    assert second_last_matrix["width"] == 2
    assert second_last_matrix["height"] == 2
    assert second_last_matrix["version"] == 2
    assert second_last_matrix["id"] == second_last_matrix_id
    assert "created_at" in second_last_matrix and is_date_format_ok

    last_matrix = matrices[-1]
    is_date_format_ok = bool(datetime.strptime(last_matrix["created_at"], time_format))
    assert last_matrix["width"] == 3
    assert last_matrix["height"] == 2
    assert last_matrix["version"] == 2
    assert last_matrix["id"] == last_matrix_id
    assert "created_at" in second_last_matrix and is_date_format_ok


def test_get_matrices_fail(client: TestClient, user_access_token: str) -> None:
    user_headers = {"Authorization": f"Bearer {user_access_token}"}

    res = client.get(
        "/v1/matrix",
        headers=user_headers,
    )
    assert res.status_code == 403
    assert res.json()["exception"] == "UserHasNotPermissionError"


def test_get_matrix(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    matrix = [[1, 2], [3, 4]]

    res = client.post(
        "/v1/matrix",
        json=matrix,
    )

    assert res.status_code == 200

    res = client.get(f"/v1/matrix/{res.json()}")

    assert res.status_code == 200
    stored = res.json()
    assert stored["id"] != ""

    matrix_id = stored["id"]

    res = client.get(f"/v1/matrix/{matrix_id}/download")
    assert res.status_code == 200

    res = client.post(
        "/v1/matrixdataset",
        json={
            "metadata": {
                "name": "mydataset",
                "groups": [],
                "public": False,
            },
            "matrices": [{"id": matrix_id, "name": "mymatrix"}],
        },
    )
    assert res.status_code == 200

    res = client.get("/v1/matrixdataset/_search?name=myda")
    results = res.json()
    assert len(results) == 1
    assert len(results[0]["matrices"]) == 1
    assert results[0]["matrices"][0]["id"] == matrix_id

    dataset_id = results[0]["id"]
    res = client.get(f"/v1/matrixdataset/{dataset_id}/download")
    assert res.status_code == 200

    res = client.delete(f"/v1/matrixdataset/{dataset_id}")
    assert res.status_code == 200
