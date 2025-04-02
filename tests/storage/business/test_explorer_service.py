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
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import ExternalWorkspaceDisabled
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolderDTO, StudyFolder, WorkspaceMetadata
from antarest.study.storage.explorer_service import Explorer


def build_config(root: Path, desktop_mode=False) -> Config:
    return Config(
        desktop_mode=desktop_mode,
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=root / DEFAULT_WORKSPACE_NAME),
                "diese": WorkspaceConfig(path=root / "diese", filter_out=[".git", ".*RECYCLE.BIN"]),
                "test": WorkspaceConfig(path=root / "test"),
            }
        ),
    )


def build_tree(root: Path) -> None:
    default = root / "default"
    default.mkdir()
    a = default / "studyA"
    a.mkdir()
    (a / "study.antares").touch()

    diese = root / "diese"
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

    d = diese / "$RECYCLE.BIN"
    d.mkdir(parents=True)
    (d / "trash").touch()


@pytest.fixture
def config_scenario_a(tmp_path: Path) -> Config:
    build_tree(tmp_path)
    config = build_config(tmp_path)
    return config


@pytest.fixture
def request_params() -> Config:
    return RequestParameters(user=JWTUser(id=1, impersonator=1, type="users"))


def config_desktop_mode(tmp_path: Path) -> Config:
    config = build_config(tmp_path, desktop_mode=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    ext_study = outside / "external_study"
    ext_study.mkdir()
    (ext_study / "study.antares").touch()
    return config


@pytest.mark.unit_test
def test_list_dir_empty_string(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, Mock())
    result = explorer.list_dir("diese", "")

    # We don't want to see the .git folder or the $RECYCLE.BIN as they were ignored in the workspace config
    assert len(result) == 1
    assert result[0] == NonStudyFolderDTO(path=Path("folder"), workspace="diese", name="folder", has_children=True)


@pytest.mark.unit_test
def test_list_dir_several_subfolders(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, Mock())
    result = explorer.list_dir("diese", "folder")

    assert len(result) == 3
    folder_path = Path("folder")
    assert (
        NonStudyFolderDTO(path=(folder_path / "subfolder1"), workspace="diese", name="subfolder1", has_children=False)
        in result
    )
    assert (
        NonStudyFolderDTO(path=(folder_path / "subfolder2"), workspace="diese", name="subfolder2", has_children=False)
        in result
    )
    assert (
        NonStudyFolderDTO(path=(folder_path / "subfolder3"), workspace="diese", name="subfolder3", has_children=False)
        in result
    )

    assert str(result[0].path) == result[0].path.as_posix()
    assert str(result[0].parent_path) == result[0].parent_path.as_posix()


@pytest.mark.unit_test
def test_list_dir_in_empty_folder(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, Mock())
    result = explorer.list_dir("diese", "folder/subfolder1")

    assert len(result) == 0


@pytest.mark.unit_test
def test_list_dir_with_permission_error(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, Mock())
    with patch("os.listdir", side_effect=PermissionError("Permission denied")):
        # asserts the endpoint doesn't fail but rather returns an empty list
        result = explorer.list_dir("diese", "folder")
        assert len(result) == 0


@pytest.mark.unit_test
def test_list_workspaces(tmp_path: Path):
    config = build_config(tmp_path)
    explorer = Explorer(config, Mock())

    result = explorer.list_workspaces()
    assert result == [WorkspaceMetadata(name="diese"), WorkspaceMetadata(name="test")]


@pytest.mark.unit_test
def test_open_external_study_success(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    path = tmp_path / Path("outside/external_study")
    study_service = Mock()
    study_service.create_external_study.return_value = "study_id_123"
    study_service.count_studies.return_value = 0
    explorer = Explorer(config, study_service)

    study_id = explorer.open_external_study(path, request_params)

    assert study_id == "study_id_123"
    study_service.create_external_study.assert_called_once_with(
        StudyFolder(path=path, workspace="external", groups=[]), request_params
    )
    study_service.count_studies.assert_called_once()


@pytest.mark.unit_test
def test_open_external_study_desktop_mode_disabled(config_scenario_a: Config, request_params: RequestParameters):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    path = Path("/valid/study/folder")

    with pytest.raises(ExternalWorkspaceDisabled, match="Desktop mode is not enabled in the configuration"):
        explorer.open_external_study(path, request_params)


@pytest.mark.unit_test
def test_open_external_study_invalid_folder(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    explorer = Explorer(config, study_service=MagicMock())
    path = Path("/invalid/folder")

    with pytest.raises(HTTPException, match="Path .* is not a study folder"):
        explorer.open_external_study(path, request_params)


@pytest.mark.unit_test
def test_open_external_study_already_exists(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    path = tmp_path / Path("outside/external_study")
    study_service = Mock()
    study_service.count_studies.return_value = 1
    explorer = Explorer(config, study_service)

    with pytest.raises(HTTPException, match="Study at .* already exists in database"):
        explorer.open_external_study(path, request_params)


@pytest.mark.unit_test
def test_open_external_study_in_default_workspace(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    path = tmp_path / DEFAULT_WORKSPACE_NAME / "study_in_default"
    path.mkdir(parents=True)
    (path / "study.antares").touch()
    study_service = Mock()
    explorer = Explorer(config, study_service)

    with pytest.raises(
        HTTPException,
        match="Path .* is inside the default workspace folder and cannot be opened as an external study",
    ):
        explorer.open_external_study(path, request_params)


@pytest.mark.unit_test
def test_close_external_study_success(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    study_service = Mock()
    explorer = Explorer(config, study_service=study_service)
    uuid = "677c1f6f-ecf7-4490-b359-b5fc50d4764d"

    explorer.close_external_study(uuid, request_params)

    study_service.delete_external_study.assert_called_once()


@pytest.mark.unit_test
def test_close_external_study_desktop_mode_disabled(config_scenario_a: Config, request_params: RequestParameters):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    uuid = "677c1f6f-ecf7-4490-b359-b5fc50d4764d"

    with pytest.raises(ExternalWorkspaceDisabled, match="Study mode is not enabled in the configuration"):
        explorer.close_external_study(uuid, request_params)


@pytest.mark.unit_test
def test_close_external_wrong_uuid_format(tmp_path: Path, request_params: RequestParameters):
    config = config_desktop_mode(tmp_path)
    explorer = Explorer(config, study_service=MagicMock())
    uuid = "xxxx"

    with pytest.raises(HTTPException, match="uuid .* is not a valid UUID"):
        explorer.close_external_study(uuid, request_params)
