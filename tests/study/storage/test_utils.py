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

from antarest.core.config import WorkspaceConfig
from antarest.study.storage.utils import is_folder_safe


@pytest.fixture
def workspace_config(tmp_path: Path) -> WorkspaceConfig:
    return WorkspaceConfig(path=tmp_path)


def test_is_folder_safe_within_workspace(workspace_config: WorkspaceConfig):
    # Test case: folder within the workspace
    folder = "project"
    assert is_folder_safe(workspace_config, folder) is True


def test_is_folder_safe_outside_workspace(workspace_config: WorkspaceConfig):
    # Test case: folder outside the workspace
    folder = "../outside"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_home_directory(workspace_config: WorkspaceConfig):
    # Test case: folder outside the workspace
    folder = "/~/project"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_traversal_attack(workspace_config: WorkspaceConfig):
    # Test case: folder with traversal attack attempt
    folder = "../../etc/passwd"
    assert is_folder_safe(workspace_config, folder) is False


def test_is_folder_safe_nested_folder(workspace_config: WorkspaceConfig):
    # Test case: nested folder within the workspace
    folder = "project/subfolder"
    assert is_folder_safe(workspace_config, folder) is True
