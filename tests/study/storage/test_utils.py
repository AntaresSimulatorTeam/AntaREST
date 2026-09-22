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

from antarest.core.utils.utils import is_path_safe
from antarest.study.storage.utils import find_single_output_path


def test_is_path_safe_within_workspace(tmp_path: Path) -> None:
    # Test case: folder within the workspace
    folder = "project"
    assert is_path_safe(tmp_path, folder) is True


def test_is_path_safe_outside_workspace(tmp_path: Path) -> None:
    # Test case: folder outside the workspace
    folder = "../outside"
    assert is_path_safe(tmp_path, folder) is False


def test_is_path_safe_home_directory(tmp_path: Path) -> None:
    # Test case: folder outside the workspace
    folder = "/~/project"
    assert is_path_safe(tmp_path, folder) is False


def test_is_path_safe_traversal_attack(tmp_path: Path) -> None:
    # Test case: folder with traversal attack attempt
    folder = "../../etc/passwd"
    assert is_path_safe(tmp_path, folder) is False


def test_is_path_safe_nested_folder(tmp_path: Path) -> None:
    # Test case: nested folder within the workspace
    folder = "project/subfolder"
    assert is_path_safe(tmp_path, folder) is True


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
