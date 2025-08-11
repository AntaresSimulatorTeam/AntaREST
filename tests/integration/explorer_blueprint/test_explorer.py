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

from antarest.study.model import FolderDTO, WorkspaceDTO

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
    directories_res = list(sorted([FolderDTO(**d) for d in directories_res], key=lambda f: f.name))
    directorires_expected = [
        FolderDTO(path=Path("folder/studyC"), workspace="ext", name="studyC", hasChildren=False, isStudyFolder=True),
        FolderDTO(path=Path("folder/trash"), workspace="ext", name="trash", hasChildren=False, isStudyFolder=False),
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
        WorkspaceDTO(
            name="ext",
        )
    ]
    res = res.json()
    res = [WorkspaceDTO(**e) for e in res]
    assert res == expected
