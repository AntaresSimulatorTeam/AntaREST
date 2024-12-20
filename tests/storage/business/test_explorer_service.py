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

from pathlib import Path
from unittest.mock import patch

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolderDTO, WorkspaceMetadata
from antarest.study.storage.explorer_service import Explorer


def build_config(root: Path) -> Config:
    return Config(
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=root / DEFAULT_WORKSPACE_NAME),
                "diese": WorkspaceConfig(path=root / "diese"),
                "test": WorkspaceConfig(path=root / "test"),
            }
        )
    )


@pytest.fixture
def config_scenario_a(tmp_path: Path) -> Config:
    default = tmp_path / "default"
    default.mkdir()
    a = default / "studyA"
    a.mkdir()
    (a / "study.antares").touch()

    diese = tmp_path / "diese"
    diese.mkdir()
    c = diese / "folder/studyC"
    c.mkdir(parents=True)
    (c / "study.antares").touch()

    d = diese / "folder/subfolder1"
    d.mkdir(parents=True)
    (d / "trash").touch()

    d = diese / "folder/subfolder2"
    d.mkdir(parents=True)
    (d / "trash").touch()

    d = diese / "folder/subfolder3"
    d.mkdir(parents=True)
    (d / "trash").touch()

    e = diese / "folder/to_skip_folder"
    e.mkdir(parents=True)
    (e / "study.antares").touch()

    f = diese / "folder/another_folder"
    f.mkdir(parents=True)
    (f / "AW_NO_SCAN").touch()
    (f / "study.antares").touch()

    d = diese / ".git"
    d.mkdir(parents=True)
    (d / "config.txt").touch()

    d = diese / "$RECYCLE.bin"
    d.mkdir(parents=True)
    (d / "trash").touch()

    config = build_config(tmp_path)

    return config


@pytest.mark.unit_test
def test_list_dir_empty_string(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
    result = explorer.list_dir("diese", "")

    assert len(result) == 1  # we don't want to see the .git folder or the $RECYCLE.BIN
    assert result[0] == NonStudyFolderDTO(path=Path("folder"), workspace="diese", name="folder")


@pytest.mark.unit_test
def test_list_dir_several_subfolders(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
    result = explorer.list_dir("diese", "folder")

    assert len(result) == 3
    folder_path = Path("folder")
    assert NonStudyFolderDTO(path=(folder_path / "subfolder1"), workspace="diese", name="subfolder1") in result
    assert NonStudyFolderDTO(path=(folder_path / "subfolder2"), workspace="diese", name="subfolder2") in result
    assert NonStudyFolderDTO(path=(folder_path / "subfolder3"), workspace="diese", name="subfolder3") in result


@pytest.mark.unit_test
def test_list_dir_in_empty_folder(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
    result = explorer.list_dir("diese", "folder/subfolder1")

    assert len(result) == 0


@pytest.mark.unit_test
def test_list_dir_with_permission_error(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
    with patch("os.listdir", side_effect=PermissionError("Permission denied")):
        # asserts the endpoint doesn't fail but rather returns an empty list
        result = explorer.list_dir("diese", "folder")
        assert len(result) == 0


@pytest.mark.unit_test
def test_list_workspaces(tmp_path: Path):
    config = build_config(tmp_path)
    explorer = Explorer(config)

    result = explorer.list_workspaces()
    assert result == [WorkspaceMetadata(name="diese"), WorkspaceMetadata(name="test")]
