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
