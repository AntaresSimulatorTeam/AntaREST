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
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.study.model import NonStudyFolderDTO, WorkspaceMetadata

OK_STATUS_CODE = 200
NOT_FOUND_STATUS_CODE = 404
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


@pytest.fixture
def study_tree_desktop(tmp_path_desktop: Path) -> Path:
    """
    Create this hierarchy

    tmp_path_desktop
    └── out_folder
        └── studyG
            └── study.antares
    """

    g = tmp_path_desktop / Path("out_folder") / Path("studyG")
    g.mkdir(parents=True)
    (g / "study.antares").touch()

    return tmp_path_desktop


def test_explorer(client: TestClient, admin_access_token: str, study_tree: Path):
    # Don't be confused here by the workspace name is "ext" being different from its folder name "ext_workspace"
    # that's just how it's configured in the "client" fixture
    workspace = "ext"

    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    res.raise_for_status()
    directories_res = res.json()
    directories_res = [NonStudyFolderDTO(**d) for d in directories_res]
    directorires_expected = [
        NonStudyFolderDTO(path=Path("folder/trash"), workspace="ext", name="trash", hasChildren=False)
    ]
    assert directories_res == directorires_expected

    # request an path where there're no folders
    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/trash",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    res.raise_for_status()
    directories_res = res.json()
    assert len(directories_res) == 0

    # request a path that isn't a folder
    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/trash/trash",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()

    # try a path traversal attack
    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder/../../",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()

    # try to access default workspase
    workspace = "default"
    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == BAD_REQUEST_STATUS_CODE

    # request a workspace that doesn't exist
    workspace = "ext2"
    res = client.get(
        f"/v1/private/explorer/{workspace}/_list_dir?path=folder",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE

    # get list of workspaces

    res = client.get(
        "/v1/private/explorer/_list_workspaces",
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

    # open external study is unavailable as desktop mode is disabled
    external_study_path = study_tree / "out_folder/studyG"
    res = client.post(
        f"/v1/private/explorer/external/_open?path={external_study_path}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == NOT_FOUND_STATUS_CODE

    # close external study is unavailable as desktop mode is disabled
    res = client.delete(
        "/v1/private/explorer/external/_close/some-uuid",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == NOT_FOUND_STATUS_CODE


def test_explorer_desktop(client_desktop: TestClient, admin_access_token: str, study_tree_desktop: Path):
    # open external study doesn't work as desktop mode is disabled
    external_study_path = study_tree_desktop / Path("out_folder") / Path("studyG")

    def assert_count(expected_count: int) -> None:
        res = client_desktop.get(
            "/v1/studies/count?name=studyG", headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        assert res.status_code == OK_STATUS_CODE
        count = res.json()
        assert count == expected_count

    # at start no study in db
    assert_count(0)

    # open one external study
    res = client_desktop.post(
        f"/v1/private/explorer/external/_open?path={external_study_path}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == OK_STATUS_CODE
    study_id = res.json()

    # check now one study is in DB
    assert_count(1)

    # open again same path
    res = client_desktop.post(
        f"/v1/private/explorer/external/_open?path={external_study_path}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == INVALID_PARAMS_STATUS_CODE

    # can't open same study twice
    assert_count(1)

    # close opened study
    res = client_desktop.delete(
        f"/v1/private/explorer/external/_close/{study_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == OK_STATUS_CODE

    # study removed from DB
    assert_count(0)

    # can't close same study twice
    res = client_desktop.delete(
        f"/v1/private/explorer/external/_close/{study_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert res.status_code == NOT_FOUND_STATUS_CODE

    # coun t hasn't changed after second close
    assert_count(0)
