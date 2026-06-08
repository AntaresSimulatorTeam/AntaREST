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

from antarest.favorite.model import FavoriteExternalDirectory
from tests.helpers import with_db_context


# TEST ADD FAVORITE EXTERNAL DIRECTORY
def test_add_favorite_external_directory_success_added_one_favorite(admin_client: TestClient, tmp_path: Path):
    favorite_path = tmp_path / "validspace" / "path" / "to" / "favorite" / "directory"
    favorite_path.mkdir(parents=True)
    favorite_external_directory_data = {"workspace": "validspace", "path": favorite_path.as_posix()}
    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data)
    assert response.status_code == 201
    json_res = response.json()
    assert json_res["path"] == favorite_external_directory_data["path"]
    assert json_res["workspace"] == favorite_external_directory_data["workspace"]

    response = admin_client.get("/v1/favorites/external_directories")
    assert response.status_code == 200
    json_res = response.json()
    assert len(json_res) == 1
    assert json_res[0]["path"] == favorite_external_directory_data["path"]
    assert json_res[0]["workspace"] == favorite_external_directory_data["workspace"]


def test_add_favorite_external_directory_failure_workspace_not_found(admin_client: TestClient, tmp_path: Path):
    favorite_path = tmp_path / "" / "path" / "to" / "favorite" / "directory"
    favorite_path.mkdir(parents=True)
    favorite_external_directory_data = {"workspace": "", "path": favorite_path.as_posix()}
    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data)
    assert response.status_code == 422
    assert response.json()["description"] == "String should have at least 1 character"


def test_add_favorite_external_directory_failure_path_not_found(admin_client: TestClient):
    invalid_test_path = "test"
    favorite_external_directory_data = {"workspace": "validspace", "path": invalid_test_path}
    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data)
    assert response.status_code == 404
    assert response.json()["description"] == f"Path {invalid_test_path} does not exist."


# TEST GET FAVORITES EXTERNAL DIRECTORY
def test_get_favorite_external_directory_success_get_one_favorite(admin_client: TestClient, tmp_path: Path):
    #adding an external directory to the favorite, and deleting it afterwards
    favorite_path = tmp_path / "validspace" / "path" / "to" / "favorite" / "directory"
    favorite_path.mkdir(parents=True)
    favorite_external_directory_data = {"workspace": "validspace", "path": favorite_path.as_posix()}
    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data)
    assert response.status_code == 201
    json_res = response.json()
    assert json_res["path"] == favorite_external_directory_data["path"]
    assert json_res["workspace"] == favorite_external_directory_data["workspace"]

    response = admin_client.get("/v1/favorites/external_directories").json()
    assert len(response) == 1
    assert response == [favorite_external_directory_data]


def test_get_favorite_external_directory_success_added_two_favorite(admin_client: TestClient,tmp_path: Path):
    favorite_workspace_1 = "validspace_1"
    favorite_path_1 = tmp_path / favorite_workspace_1 / "path" / "to" / "favorite" / "directory"
    favorite_path_1.mkdir(parents=True)
    favorite_external_directory_data_1 = {"workspace": favorite_workspace_1, "path": favorite_path_1.as_posix()}

    favorite_workspace_2 = "validspace_2"
    favorite_path_2 = tmp_path / favorite_workspace_2 / "path" / "to" / "favorite" / "directory"
    favorite_path_2.mkdir(parents=True)
    favorite_external_directory_data_2 = {"workspace": favorite_workspace_2, "path": favorite_path_2.as_posix()}

    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data_1)
    assert response.status_code == 201
    json_res = response.json()
    assert json_res["path"] == favorite_external_directory_data_1["path"]
    assert json_res["workspace"] == favorite_external_directory_data_1["workspace"]

    json_res = admin_client.get("/v1/favorites/external_directories").json()
    assert len(json_res) == 1

    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data_2)
    assert response.status_code == 201
    json_res = response.json()
    assert json_res["path"] == favorite_external_directory_data_2["path"]
    assert json_res["workspace"] == favorite_external_directory_data_2["workspace"]

    json_res = admin_client.get("/v1/favorites/external_directories").json()
    assert len(json_res) == 2
    assert json_res == [favorite_external_directory_data_1, favorite_external_directory_data_2]


# TEST DELETE FAVORITE EXTERNAL DIRECTORY
def test_delete_favorite_external_directory_success_deleted_one_favorite(admin_client: TestClient, tmp_path: Path):
    favorite_workspace_1 = "validspace"
    favorite_path_1 = tmp_path / favorite_workspace_1 / "path" / "to" / "favorite" / "directory"
    favorite_path_1.mkdir(parents=True)

    favorite_external_directory_data = {"workspace": favorite_workspace_1, "path": favorite_path_1.as_posix()}

    response = admin_client.post("/v1/favorites/external_directories", params=favorite_external_directory_data)
    assert response.status_code == 201

    admin_client.delete(f"/v1/favorites/external_directories", params=favorite_external_directory_data)
    response = admin_client.get("/v1/favorites/external_directories").json()
    assert len(response) == 0


def test_delete_favorite_external_directory_failure_not_found(admin_client: TestClient):
    pass
