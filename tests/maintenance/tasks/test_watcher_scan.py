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

"""Tests for watcher scan task."""

from unittest.mock import Mock

import pytest

from antarest.core.config import StorageConfig, WorkspaceConfig
from antarest.maintenance.tasks.watcher_scan import _collect_studies
from antarest.maintenance.tasks.watcher_scan_task import watcher_scan_task


class TestCollectStudies:
    def test_returns_empty_list_when_no_studies(self, tmp_path: str) -> None:
        workspace_path = tmp_path / "workspace1"
        workspace_path.mkdir()
        config = Mock()
        config.storage = StorageConfig(
            workspaces={
                "default": WorkspaceConfig(path=tmp_path / "default"),
                "workspace1": WorkspaceConfig(
                    path=workspace_path,
                    groups=["group1"],
                    filter_in=[".*"],
                    filter_out=[],
                ),
            }
        )

        result = _collect_studies(config)

        assert result == []

    def test_finds_studies_in_workspaces(self, tmp_path: str) -> None:
        workspace_path = tmp_path / "workspace1"
        workspace_path.mkdir()
        # Create a study in the workspace
        study_path = workspace_path / "my_study"
        study_path.mkdir()
        (study_path / "study.antares").touch()

        config = Mock()
        config.storage = StorageConfig(
            workspaces={
                "default": WorkspaceConfig(path=tmp_path / "default"),
                "workspace1": WorkspaceConfig(
                    path=workspace_path,
                    groups=["group1"],
                    filter_in=[".*"],
                    filter_out=[],
                ),
            }
        )

        result = _collect_studies(config)

        assert len(result) == 1
        assert result[0].path == study_path

    def test_skips_default_workspace(self, tmp_path: str) -> None:
        # Create a study in the default workspace - it should be ignored
        default_path = tmp_path / "default"
        default_path.mkdir()
        study_in_default = default_path / "study_to_ignore"
        study_in_default.mkdir()
        (study_in_default / "study.antares").touch()

        config = Mock()
        config.storage = StorageConfig(
            workspaces={
                "default": WorkspaceConfig(path=default_path),
            }
        )

        result = _collect_studies(config)

        assert result == []

    def test_finds_studies_in_multiple_workspaces(self, tmp_path: str) -> None:
        workspace1_path = tmp_path / "workspace1"
        workspace1_path.mkdir()
        workspace2_path = tmp_path / "workspace2"
        workspace2_path.mkdir()

        # Create studies
        study1 = workspace1_path / "study1"
        study1.mkdir()
        (study1 / "study.antares").touch()

        study2 = workspace2_path / "study2"
        study2.mkdir()
        (study2 / "study.antares").touch()

        config = Mock()
        config.storage = StorageConfig(
            workspaces={
                "default": WorkspaceConfig(path=tmp_path / "default"),
                "workspace1": WorkspaceConfig(
                    path=workspace1_path,
                    groups=[],
                    filter_in=[".*"],
                    filter_out=[],
                ),
                "workspace2": WorkspaceConfig(
                    path=workspace2_path,
                    groups=[],
                    filter_in=[".*"],
                    filter_out=[],
                ),
            }
        )

        result = _collect_studies(config)

        assert len(result) == 2


class TestWatcherScanTask:
    def test_raises_without_context(self, with_no_maintenance_ctx: None) -> None:
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            watcher_scan_task.run()
