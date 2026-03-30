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
import uuid

from starlette.testclient import TestClient


def test_favorite_directory(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # creating empty directories

    directory_test_1 = client.post("/v1/directories", json={"name": "directory_test_1"}).json()
    directory_test_2 = client.post("/v1/directories", json={"name": "directory_test_2"}).json()
    dt_1_id = directory_test_1["id"]
    dt_2_id = directory_test_2["id"]
    # adding favorite directories and checking the API returns the good amount of favorites
    dto_test_1 = {"directoryId": dt_1_id, "directoryName": "directory_test_1"}
    dto_test_2 = {"directoryId": dt_2_id, "directoryName": "directory_test_2"}

    resp = client.post(f"/v1/favorites/directories/{dt_1_id}")
    assert resp.status_code == 200
    directory_dto_1 = resp.json()
    assert directory_dto_1["directoryId"] == dt_1_id
    assert directory_dto_1["directoryName"] == "directory_test_1"

    resp = client.post(f"/v1/favorites/directories/{dt_2_id}")
    assert resp.status_code == 200
    directory_dto_2 = resp.json()
    assert directory_dto_2["directoryId"] == dt_2_id
    assert directory_dto_2["directoryName"] == "directory_test_2"

    actual_favorite_directories_list = client.get("/v1/favorites/directories").json()
    expected_favorite_directories_list = [dto_test_1, dto_test_2]

    assert actual_favorite_directories_list == expected_favorite_directories_list

    resp = client.delete(f"/v1/favorites/directories/{dt_1_id}")
    assert resp.status_code == 200
    expected_favorite_directories_list.remove(directory_dto_1)
    actual_favorite_directories_list = client.get("/v1/favorites/directories").json()

    assert actual_favorite_directories_list == [directory_dto_2]

    resp = client.delete(f"/v1/favorites/directories/{dt_2_id}")
    assert resp.status_code == 200
    actual_favorite_directories_list = client.get("/v1/favorites/directories").json()

    assert actual_favorite_directories_list == []


def test_delete_directory(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # creating empty directories

    directory_test_1 = client.post("/v1/directories", json={"name": "directory_test_1"}).json()
    directory_test_2 = client.post("/v1/directories", json={"name": "directory_test_2"}).json()
    dt_1_id = directory_test_1["id"]
    dt_2_id = directory_test_2["id"]

    # adding favorite directories and checking the API returns the good amount of favorites
    dto_test_1 = {"directoryId": dt_1_id, "directoryName": "directory_test_1"}
    dto_test_2 = {"directoryId": dt_2_id, "directoryName": "directory_test_2"}

    resp = client.post(f"/v1/favorites/directories/{dt_1_id}")
    assert resp.status_code == 200
    assert resp.json()["directoryId"] == dt_1_id
    resp = client.post(f"/v1/favorites/directories/{dt_2_id}")
    assert resp.status_code == 200
    assert resp.json()["directoryId"] == dt_2_id

    actual_favorite_directories = client.get("/v1/favorites/directories").json()
    assert actual_favorite_directories == [dto_test_1, dto_test_2]

    # directly deleting directories to see if the favorites disappear the same way
    resp_delete = client.delete(f"/v1/directories/{dt_1_id}")
    assert resp_delete.status_code == 204

    actual_favorite_directories = client.get("/v1/favorites/directories").json()
    assert actual_favorite_directories == [dto_test_2]

    resp_delete = client.delete(f"/v1/directories/{dt_2_id}")
    assert resp_delete.status_code == 204

    actual_favorite_directories = client.get("/v1/favorites/directories").json()
    assert actual_favorite_directories == []


def test_add_inexisting_directory_failure(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # trying to add an inexisting directory to the favorite
    inexisting_directory_id = str(uuid.uuid4())

    resp_add = client.post(f"/v1/favorites/directories/{inexisting_directory_id}")
    assert resp_add.status_code == 404
    assert resp_add.json()["description"] == f"Directory with id {inexisting_directory_id} not found"


def test_delete_inexisting_directory_failure(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # trying to delete an inexisting directory to the favorite
    inexisting_directory_id = str(uuid.uuid4())

    resp_delete = client.delete(f"/v1/favorites/directories/{inexisting_directory_id}")
    assert resp_delete.status_code == 404
    assert resp_delete.json()["description"] == f"Directory with id {inexisting_directory_id} not found"


def test_add_favorite_directory_already_existing(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    directory_test_1 = client.post("/v1/directories", json={"name": "directory_test_1"}).json()
    dt_1_id = directory_test_1["id"]

    dto_test = {"directoryId": dt_1_id, "directoryName": "directory_test_1"}

    resp = client.post(f"/v1/favorites/directories/{dt_1_id}")
    assert resp.status_code == 200
    resp_list = client.get("/v1/favorites/directories").json()
    assert resp_list == [dto_test]

    # adding the same directory to the favorite to see if it remains the same
    resp = client.post(f"/v1/favorites/directories/{dt_1_id}")
    assert resp.status_code == 200
    resp_list = client.get("/v1/favorites/directories").json()
    assert resp_list == [dto_test]
