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
from pathlib import Path, PurePosixPath

from starlette.testclient import TestClient


# TEST ADD FAVORITE EXTERNAL DIRECTORY
def test_add_favorite_external_directory_success_added_one_favorite(admin_client: TestClient, tmp_path: Path):

    workspace_name = "default"
    path = "path/to/favorite/directory"
    path_ws = tmp_path / "internal_workspace" / workspace_name / path
    path_ws.mkdir(parents=True, exist_ok=True)
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(path_ws)}
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 201
    actual_favorite_external_directory = response.json()

    assert actual_favorite_external_directory["workspace"] == workspace_name
    assert actual_favorite_external_directory["path"] == str(PurePosixPath(path))


def test_add_favorite_external_directory_failure_workspace_not_found(admin_client: TestClient, tmp_path: Path):
    workspace_name = "workspace_not_found"
    path = "path/to/favorite/directory"
    path_ws = tmp_path / "internal_workspace" / workspace_name / path
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(path_ws)}
    path_ws.mkdir(parents=True, exist_ok=True)
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 422
    assert response.json()["description"] == f"Workspace {workspace_name} not found"


def test_add_favorite_external_directory_failure_path_not_found(admin_client: TestClient, tmp_path: Path):
    # checking that the favorite external directory is not added if the path does not exist
    workspace_name = "default"
    path = tmp_path / "internal_workspace" / workspace_name
    path.mkdir(parents=True, exist_ok=True)
    inexisting_dir = path / "inexisting_dir" / "to" / "favorite" / "directory"
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(inexisting_dir)}
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 404
    assert response.json()["description"] == f"Directory '{inexisting_dir}' not found"


def test_add_favorite_external_directory_failure_folder_not_safe(admin_client: TestClient, tmp_path: Path):
    # checking that the favorite external directory is not added if the path is not safe
    workspace_name = "default"
    path = tmp_path / workspace_name
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(path)}
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 400
    assert response.json()["description"] == f"Directory {path} is not safe"


# TEST GET FAVORITES EXTERNAL DIRECTORY
def test_get_favorite_external_directory_success_get_one_favorite(admin_client: TestClient, tmp_path: Path):
    # creating one favorite external directory and checking that it is returned
    workspace_name = "default"
    path = "path/to/favorite/directory"
    path_ws = tmp_path / "internal_workspace" / workspace_name / path
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(path_ws)}
    path_ws.mkdir(parents=True, exist_ok=True)
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 201
    actual_favorite_list = admin_client.get("/v1/favorites/external_directories").json()
    assert len(actual_favorite_list) == 1
    assert actual_favorite_list[0]["workspace"] == workspace_name
    assert actual_favorite_list[0]["path"] == str(PurePosixPath(path))


def test_get_favorite_external_directory_success_added_two_favorite(admin_client: TestClient, tmp_path: Path):
    # creating two favorite external directories and checking that they are returned
    workspace_name = "default"
    path_1 = "path/to/favorite/directory_1"
    path_2 = "path/to/favorite/directory_2"
    path_ws_1 = tmp_path / "internal_workspace" / workspace_name / path_1
    path_ws_2 = tmp_path / "internal_workspace" / workspace_name / path_2
    expected_favorite_external_directory_1 = {"workspace": workspace_name, "path": str(path_ws_1)}
    expected_favorite_external_directory_2 = {"workspace": workspace_name, "path": str(path_ws_2)}
    path_ws_1.mkdir(parents=True, exist_ok=True)
    path_ws_2.mkdir(parents=True, exist_ok=True)
    response_1 = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory_1)
    assert response_1.status_code == 201
    response_2 = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory_2)
    assert response_2.status_code == 201
    actual_favorite_list = admin_client.get("/v1/favorites/external_directories").json()
    assert len(actual_favorite_list) == 2
    expected_favorite_external_directory_1["path"] = str(PurePosixPath(path_1))
    expected_favorite_external_directory_2["path"] = str(PurePosixPath(path_2))
    assert actual_favorite_list == [expected_favorite_external_directory_1, expected_favorite_external_directory_2]


# TEST DELETE FAVORITE EXTERNAL DIRECTORY
def test_delete_favorite_external_directory_success_deleted_one_favorite(admin_client: TestClient, tmp_path: Path):
    # adding an external directory to the favorite, and deleting it afterwards
    workspace_name = "default"
    path = "path/to/favorite/directory"
    path_ws = tmp_path / "internal_workspace" / workspace_name / path
    expected_favorite_external_directory = {"workspace": workspace_name, "path": str(path_ws)}
    path_ws.mkdir(parents=True, exist_ok=True)
    response = admin_client.post("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 201
    actual_favorite_list = admin_client.get("/v1/favorites/external_directories").json()
    expected_favorite_external_directory["path"] = str(PurePosixPath(path))
    assert actual_favorite_list == [expected_favorite_external_directory]

    admin_client.delete("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    actual_favorite_list = admin_client.get("/v1/favorites/external_directories").json()
    assert actual_favorite_list == []


def test_delete_favorite_external_directory_failure_not_found(admin_client: TestClient):
    # trying to delete a favorite external directory that does not exist
    path = "path/to/favorite/directory"
    workspace_name = "default"
    expected_favorite_external_directory = {"workspace": workspace_name, "path": path}
    response = admin_client.delete("/v1/favorites/external_directories", params=expected_favorite_external_directory)
    assert response.status_code == 404
    assert (
        response.json()["description"]
        == f"Favorite external directory with path {path} and workspace {workspace_name} not found"
    )
