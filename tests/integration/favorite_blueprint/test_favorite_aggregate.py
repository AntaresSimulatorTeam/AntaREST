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
from pathlib import Path

from starlette.testclient import TestClient


def test_favorite_aggregate_success_no_favorite_added(admin_client: TestClient):
    # using the aggregate method in order to check that no favorite is present when called
    aggregate_res = admin_client.get("/v1/favorites").json()
    assert aggregate_res["studies"] == []
    assert aggregate_res["directories"] == []
    assert aggregate_res["externalDirectories"] == []


def test_favorite_aggregate_success_added_each_type_of_favorite(admin_client: TestClient, tmp_path: Path):
    workspace_name = "ext"
    path = Path("path") / "to" / "favorite" / "directory"
    path_ws = tmp_path / "ext_workspace" / path
    path_ws.mkdir(parents=True, exist_ok=True)
    expected_favorite_external_directory = {"workspace": workspace_name, "path": path.as_posix()}

    # creating a study, a directory and an external directory, adding them as favorites and checking that they are returned
    study_response = admin_client.post("v1/studies", params={"name": "Test Study for Favorites"})
    directory_response = admin_client.post("v1/directories", json={"name": "Test Directory for Favorites"})
    dir_id = directory_response.json()["id"]
    fav_study_response = admin_client.post(f"v1/favorites/studies/{study_response.json()}")
    fav_directory_response = admin_client.post(f"v1/favorites/directories/{dir_id}")
    fav_ext_directory_response = admin_client.post(
        "v1/favorites/external-directories", params=expected_favorite_external_directory
    )
    aggregate_res = admin_client.get("/v1/favorites").json()

    fav_ext_directory_response.json()["path"] = path.as_posix()

    assert aggregate_res == {
        "directories": [fav_directory_response.json()],
        "externalDirectories": [fav_ext_directory_response.json()],
        "studies": [fav_study_response.json()],
    }


def test_favorite_aggregate_success_one_user_added_two_favorites_that_cant_be_seen_by_another_user(
    admin_client: TestClient, user_access_token: str
):
    study_response = admin_client.post(
        "/v1/studies",
        params={"name": "Test Study for Favorites"},
    )
    assert study_response.status_code == 201
    study_id = study_response.json()

    # Add the study to favorites
    study_res = admin_client.post(f"/v1/favorites/studies/{study_id}")
    assert study_res.status_code == 201

    # Add a directory to favorites
    # Create directory structure 'foo/bar' before moving the study
    res = admin_client.post(
        "/v1/directories",
        json={"name": "foo"},
    )
    assert res.status_code == 201, res.json()

    directory_id = res.json()["id"]
    directory_res = admin_client.post(f"/v1/favorites/directories/{directory_id}")
    assert directory_res.status_code == 201

    # Verify the study appears in the aggregate
    aggregate_res = admin_client.get("/v1/favorites").json()
    assert len(aggregate_res["studies"]) == 1
    assert aggregate_res["studies"][0]["studyId"] == study_id
    assert aggregate_res["studies"][0]["studyName"] == "Test Study for Favorites"
    assert aggregate_res["directories"][0]["directoryId"] == directory_id
    assert aggregate_res["directories"][0]["directoryName"] == "foo"

    # next thing : another user gets one of those favorites and checks that it's not there'
    admin_client.headers = {"Authorization": f"Bearer {user_access_token}"}

    response = admin_client.get("/v1/favorites").json()
    assert response == {"directories": [], "externalDirectories": [], "studies": []}

    # Next thing : the other user adds the favorites and checks that they are there
    directory_res = admin_client.post(f"/v1/favorites/directories/{directory_id}").json()
    study_res = admin_client.post(f"/v1/favorites/studies/{study_id}").json()
    aggregate_res = admin_client.get("/v1/favorites").json()
    assert aggregate_res == {"directories": [directory_res], "externalDirectories": [], "studies": [study_res]}
