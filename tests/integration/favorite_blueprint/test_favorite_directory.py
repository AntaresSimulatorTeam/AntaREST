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

from starlette.testclient import TestClient


def test_favorite_directory(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # creating empty directories

    directory_test_1 = client.post("/v1/directories", json={"name": "directory_test_1"}).json()
    directory_test_2 = client.post("/v1/directories", json={"name": "directory_test_2"}).json()
    dt_1_id = directory_test_1["id"]
    dt_2_id = directory_test_2["id"]
    # adding favorite directories and checking the API returns the good amount of favorites

    resp = client.post(f"/v1/favorite/directories/{dt_1_id}")
    assert resp.status_code == 200
    directory_dto_1 = resp.json()
    resp = client.post(f"/v1/favorite/directories/{dt_2_id}")
    assert resp.status_code == 200
    directory_dto_2 = resp.json()

    actual_favorite_directories_list = client.get("/v1/favorite/directories").json()
    expected_favorite_directories_list = [directory_dto_1, directory_dto_2]

    assert actual_favorite_directories_list == expected_favorite_directories_list

    resp = client.delete(f"/v1/favorite/directories/{dt_1_id}")
    assert resp.status_code == 200
    expected_favorite_directories_list.remove(directory_dto_1)
    actual_favorite_directories_list = client.get("/v1/favorite/directories").json()

    assert actual_favorite_directories_list == expected_favorite_directories_list

    resp = client.delete(f"/v1/favorite/directories/{dt_2_id}")
    assert resp.status_code == 200
    expected_favorite_directories_list.remove(directory_dto_2)
    actual_favorite_directories_list = client.get("/v1/favorite/directories").json()

    assert actual_favorite_directories_list == expected_favorite_directories_list
