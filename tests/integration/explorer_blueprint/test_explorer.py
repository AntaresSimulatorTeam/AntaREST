# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import typing as t
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.model import NonStudyFolder, WorkspaceMetadata

BAD_REQUEST_STATUS_CODE = 400
# Status code for directory listing with invalid parameters
INVALID_PARAMS_STATUS_CODE = 422


@pytest.fixture
def study_tree(tmp_path: Path) -> Path:
    """
    Create this hierarchy

    tmp_path
    └── ext_workspace
        └── folder
            ├── studyC
            │   └── study.antares
            ├── trash
            │   └── trash
            ├── another_folder
            │   ├── AW_NO_SCAN
            │   └── study.antares
            └── subfolder
                └── studyG
                    └── study.antares
    """
    ext_workspace = tmp_path / "ext_workspace"
    c = ext_workspace / "folder/studyC"
    c.mkdir(parents=True)
    (c / "study.antares").touch()

    d = ext_workspace / "folder/trash"
    d.mkdir(parents=True)
    (d / "trash").touch()

    f = ext_workspace / "folder/another_folder"
    f.mkdir(parents=True)
    (f / "AW_NO_SCAN").touch()
    (f / "study.antares").touch()

    return tmp_path


def test_explorer(app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path):
    workspace = "ext"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    res.raise_for_status()
    directories_res = res.json()
    directories_res = [NonStudyFolder(**d) for d in directories_res]
    directorires_expected = [
        NonStudyFolder(
            path=f"{study_tree}/ext_workspace/folder/trash",
            workspace="ext",
            name="trash",
        )
    ]
    assert directories_res == directorires_expected


def test_explorer_no_directories(app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path):
    workspace = "ext"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/trash",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    res.raise_for_status()
    directories_res = res.json()
    assert len(directories_res) == 0


def test_explorer_path_is_not_dir(app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path):
    workspace = "ext"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/trash/trash",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()


def test_explorer_path_traversal_attempt(app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path):
    workspace = "ext"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/../../",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()


def test_explorer_access_default_folder_attempt(
    app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path
):
    workspace = "default"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == BAD_REQUEST_STATUS_CODE


def test_explorer_access_not_found_workspace_attempt(
    app: FastAPI, client: TestClient, admin_access_token: str, study_tree: Path
):
    workspace = "crazyworkspace"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE


def test_explorer_list_workspaces(app: FastAPI, client: TestClient, admin_access_token: str):
    res = client.get(
        f"/v1/private/explorer/_list_workspaces",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    expected = [
        WorkspaceMetadata(
            name="ext",
        )
    ]
    res = res.json()
    res = [WorkspaceMetadata(**e) for e in res]
    assert res == expected
