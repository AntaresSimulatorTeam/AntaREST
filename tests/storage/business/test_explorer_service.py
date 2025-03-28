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

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.model import StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.study.main import build_study_service
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolderDTO, StudyFolder, WorkspaceMetadata
from antarest.study.storage.explorer_service import Explorer


def build_config(root: Path) -> Config:
    return Config(
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=root / DEFAULT_WORKSPACE_NAME),
                "diese": WorkspaceConfig(path=root / "diese", filter_out=[".git", ".*RECYCLE.BIN"]),
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

    d = diese / "$RECYCLE.BIN"
    d.mkdir(parents=True)
    (d / "trash").touch()

    config = build_config(tmp_path)

    return config


@pytest.mark.unit_test
def test_list_dir_empty_string(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
    result = explorer.list_dir("diese", "")

    # We don't want to see the .git folder or the $RECYCLE.BIN as they were ignored in the workspace config
    assert len(result) == 1
    assert result[0] == NonStudyFolderDTO(path=Path("folder"), workspace="diese", name="folder", has_children=True)


@pytest.mark.unit_test
def test_list_dir_several_subfolders(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a)
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


@pytest.mark.unit_test
def test_open_external_study_success(config_scenario_a: Config):
    repository = Mock()
    # repository.get_all_raw.side_effect = []
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    study_service = build_study_service(Mock(), repository, config)

    explorer = Explorer(config_scenario_a, study_service)
    explorer.config.desktop_mode = True
    path = Path("/valid/study/folder")
    params = RequestParameters(user="test_user")

    with (
        patch("antarest.study.storage.explorer_service.is_study_folder", return_value=True),
        patch("antarest.study.storage.explorer_service.should_ignore_folder_for_scan", return_value=False),
        patch.object(explorer.study_service, "create_external_study", return_value="study_id_123"),
    ):
        study_id = explorer.open_external_study(path, params)

    assert study_id == "study_id_123"
    repository.save.assert_called_once_with(StudyFolder(path=path, workspace="external", groups=[]), params)


@pytest.mark.unit_test
def test_open_external_study_desktop_mode_disabled(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = False
    path = Path("/valid/study/folder")
    params = RequestParameters(user="test_user")

    with pytest.raises(ValueError, match="Study mode is not enabled in the configuration"):
        explorer.open_external_study(path, params)


@pytest.mark.unit_test
def test_open_external_study_invalid_folder(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = True
    path = Path("/invalid/folder")
    params = RequestParameters(user="test_user")

    with patch("antarest.study.storage.explorer_service.is_study_folder", return_value=False):
        with pytest.raises(ValueError, match=f"Path {path} is not a study folder"):
            explorer.open_external_study(path, params)


@pytest.mark.unit_test
def test_open_external_study_filtered_folder(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = True
    path = Path("/filtered/folder")
    params = RequestParameters(user="test_user")

    with (
        patch("antarest.study.storage.explorer_service.is_study_folder", return_value=True),
        patch("antarest.study.storage.explorer_service.should_ignore_folder_for_scan", return_value=True),
    ):
        with pytest.raises(ValueError, match="Can't to open a file in a filtered folder"):
            explorer.open_external_study(path, params)


@pytest.mark.unit_test
def test_open_external_study_already_exists(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = True
    path = Path("/existing/study/folder")
    params = RequestParameters(user="test_user")

    with (
        patch("antarest.study.storage.explorer_service.is_study_folder", return_value=True),
        patch("antarest.study.storage.explorer_service.should_ignore_folder_for_scan", return_value=False),
        patch.object(explorer.study_service, "count_studies", return_value=1),
    ):
        with pytest.raises(ValueError, match=f"Study at {path} already exists in database"):
            explorer.open_external_study(path, params)


@pytest.mark.unit_test
def test_close_external_study_success(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = True
    uuid = "study_uuid_123"
    params = RequestParameters(user="test_user")

    with (
        patch("antarest.study.storage.explorer_service.sanitize_uuid", return_value=uuid),
        patch.object(explorer.study_service, "check_study_access") as mock_check_access,
        patch.object(explorer.study_service, "delete_external_study") as mock_delete_study,
    ):
        explorer.close_external_study(uuid, params)

    mock_check_access.assert_called_once_with(uuid, StudyPermissionType.WRITE, params)
    mock_delete_study.assert_called_once()


@pytest.mark.unit_test
def test_close_external_study_desktop_mode_disabled(config_scenario_a: Config):
    explorer = Explorer(config_scenario_a, study_service=MagicMock())
    explorer.config.desktop_mode = False
    uuid = "study_uuid_123"
    params = RequestParameters(user="test_user")

    with pytest.raises(ValueError, match="Study mode is not enabled in the configuration"):
        explorer.close_external_study(uuid, params)
