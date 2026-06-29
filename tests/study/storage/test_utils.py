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

import pytest

from antarest.core.config import WorkspaceConfig
from antarest.study.storage.utils import find_single_output_path, is_folder_safe


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


def test_find_single_output_path_normal(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    sim_dir = output_dir / "20241201-1200eco"
    sim_dir.mkdir(parents=True)
    (sim_dir / "info.antares-output").touch()
    (sim_dir / "economy").mkdir()  # multiple children → no recursion
    assert find_single_output_path(output_dir) == sim_dir


def test_find_single_output_path_zip(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    zip_file = output_dir / "result.zip"
    zip_file.touch()
    assert find_single_output_path(output_dir) == zip_file


def test_find_single_output_path_failed_launch_returns_file(tmp_path: Path) -> None:
    # A failed launch leaves only simulation.log; must return the file, not crash.
    output_dir = tmp_path / "output"
    sim_dir = output_dir / "20241201-1200eco"
    sim_dir.mkdir(parents=True)
    log_file = sim_dir / "simulation.log"
    log_file.write_text("solver crashed")
    assert find_single_output_path(output_dir) == log_file
