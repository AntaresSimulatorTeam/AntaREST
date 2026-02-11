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


def test_favorite_study(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # creating empty studies

    study_test_1 = client.post("/v1/studies?name=study_1").json()
    study_test_2 = client.post("/v1/studies?name=study_2").json()

    # adding favorites and checking the API returns the good number

    resp = client.post(f"/v1/favorites/studies/{study_test_1}")
    assert resp.status_code == 200
    resp = client.post(f"/v1/favorites/studies/{study_test_2}")
    assert resp.status_code == 200
    fav_study_dto_1 = {"study_id": study_test_1, "study_name": "study_1"}
    fav_study_dto_2 = {"study_id": study_test_2, "study_name": "study_2"}
    expected_favorite_list = [fav_study_dto_1, fav_study_dto_2]

    favorite_list = client.get("/v1/favorites/studies").json()
    assert favorite_list == expected_favorite_list

    # deleting studies from favorites

    client.delete(f"/v1/favorites/studies/{study_test_1}")
    favorite_list = client.get("/v1/favorites/studies").json()
    assert favorite_list == [fav_study_dto_2]

    client.delete(f"/v1/favorites/studies/{study_test_2}")
    favorite_list = client.get("/v1/favorites/studies").json()
    assert favorite_list == []


def test_directly_delete_study(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # creating empty studies
    study_test_1 = client.post("/v1/studies?name=study_1").json()
    study_test_2 = client.post("/v1/studies?name=study_2").json()

    # adding favorites and checking the API returns the good number

    resp = client.post(f"/v1/favorites/studies/{study_test_1}")
    assert resp.status_code == 200
    resp = client.post(f"/v1/favorites/studies/{study_test_2}")
    assert resp.status_code == 200
    fav_study_dto_1 = {"study_id": study_test_1, "study_name": "study_1"}
    fav_study_dto_2 = {"study_id": study_test_2, "study_name": "study_2"}

    actual_favorite_studies = client.get("/v1/favorites/studies").json()
    assert actual_favorite_studies == [fav_study_dto_1, fav_study_dto_2]

    resp_delete = client.delete(f"/v1/studies/{study_test_1}")
    assert resp_delete.status_code == 200
    actual_favorite_studies = client.get("/v1/favorites/studies").json()
    assert actual_favorite_studies == [fav_study_dto_2]

    resp_delete = client.delete(f"/v1/studies/{study_test_2}")
    assert resp_delete.status_code == 200
    actual_favorite_studies = client.get("/v1/favorites/studies").json()
    assert actual_favorite_studies == []


def test_add_favorite_study_failure_not_found(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    inexisting_study_id = str(uuid.uuid4())

    resp = client.post(f"/v1/favorites/studies/{inexisting_study_id}")
    assert resp.status_code == 404
    assert resp.json()["description"] == f"Study with id {inexisting_study_id} not found"


def test_delete_favorite_study_failure_not_found(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    inexisting_study_id = str(uuid.uuid4())

    resp = client.delete(f"/v1/favorites/studies/{inexisting_study_id}")
    assert resp.status_code == 404
    assert resp.json()["description"] == f"Study with id {inexisting_study_id} not found"


def test_add_favorite_study_already_existing(client: TestClient, admin_access_token: str):
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    study_test_1 = client.post("/v1/studies?name=study_test").json()
    dto_test = {"study_id": study_test_1, "study_name": "study_test"}

    resp = client.post(f"/v1/favorites/studies/{study_test_1}")
    assert resp.status_code == 200
    resp_list = client.get("/v1/favorites/studies").json()
    assert resp_list == [dto_test]

    resp = client.post(f"/v1/favorites/studies/{study_test_1}")
    assert resp.status_code == 200
    resp_list = client.get("/v1/favorites/studies").json()
    assert resp_list == [dto_test]
