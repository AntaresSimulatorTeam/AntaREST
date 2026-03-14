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
from unittest.mock import Mock

import pytest

from antarest.core.config import WorkspaceConfig
from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.core.utils.utils import current_time
from antarest.login.model import Group
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.utils import is_folder_safe, rec_scan_for_studies, update_antares_info
from tests.helpers import create_study


@pytest.fixture
def workspace_config(tmp_path: Path) -> WorkspaceConfig:
    return WorkspaceConfig(path=tmp_path)


def test_is_folder_safe_within_workspace(workspace_config: WorkspaceConfig) -> None:
    # Test case: folder within the workspace
    folder = "project"
    assert is_folder_safe(workspace_config, folder) is True


def test_is_folder_safe_outside_workspace(workspace_config: WorkspaceConfig) -> None:
    # Test case: folder outside the workspace
    folder = "../outside"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_home_directory(workspace_config: WorkspaceConfig) -> None:
    # Test case: folder outside the workspace
    folder = "/~/project"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_traversal_attack(workspace_config: WorkspaceConfig) -> None:
    # Test case: folder with traversal attack attempt
    folder = "../../etc/passwd"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_nested_folder(workspace_config: WorkspaceConfig) -> None:
    # Test case: nested folder within the workspace
    folder = "project/subfolder"
    assert is_folder_safe(workspace_config, folder) is True


@pytest.mark.parametrize(
    "version,expected_version",
    [
        ("8.8", "880"),
        ("880", "880"),
        ("9.2", "9.2"),
        ("920", "9.2"),
    ],
)
def test_update_antares_info_version(tmp_path: Path, version: str, expected_version: str) -> None:
    """
    Checks that version field is formatted correctly, depending on study version.
    """

    study_path = tmp_path / "study"
    study_path.mkdir()
    config = FileStudyTreeConfig(study_path=study_path, path=study_path, study_id="my-study", version=STUDY_VERSION_8_8)
    tree = FileStudyTree(matrix_mapper=Mock(), config=config)
    antares_study_path = study_path / "study.antares"
    write_ini_file(antares_study_path, {"antares": {"version": "700"}})

    now = current_time()
    metadata = create_study(name="my-study", version=version, created_at=now, updated_at=now)
    update_antares_info(metadata, tree, update_author=False)
    updated = read_ini(antares_study_path)
    assert str(updated["antares"]["version"]) == expected_version


def test_rec_scan_for_studies_ignores_aw_no_scan(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    valid_study = workspace / "valid_study"
    valid_study.mkdir()
    (valid_study / "study.antares").touch()

    ignored_study = workspace / "ignored_study"
    ignored_study.mkdir()
    (ignored_study / "AW_NO_SCAN").touch()
    (ignored_study / "study.antares").touch()

    studies = rec_scan_for_studies(workspace, "workspace", [Group(id="g", name="g")], [".*"], [])

    assert {study.path for study in studies} == {valid_study}


def test_rec_scan_for_studies_returns_root_study_with_zero_max_depth(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "study.antares").touch()

    studies = rec_scan_for_studies(workspace, "workspace", [Group(id="g", name="g")], [".*"], [], max_depth=0)

    assert len(studies) == 1
    assert studies[0].path == workspace
