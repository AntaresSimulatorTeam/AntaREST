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

from unittest.mock import Mock, patch

import pytest

from antarest.core.config import StorageConfig, WorkspaceConfig
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.watcher_scan import scan_workspaces
from antarest.maintenance.tasks.watcher_scan_task import watcher_scan_task


class TestScanWorkspaces:
    @pytest.fixture
    def mock_config(self, tmp_path):
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
        return config

    @pytest.fixture
    def mock_study_service(self):
        return Mock()

    def test_returns_success_when_no_studies(self, mock_config, mock_study_service):
        with (
            patch("antarest.maintenance.tasks.watcher_scan.db"),
            patch("antarest.maintenance.tasks.watcher_scan.create_lock"),
        ):
            result = scan_workspaces(mock_config, mock_study_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.studies_found == 0
        assert result.dry_run is False

    def test_finds_studies_in_workspaces(self, mock_config, mock_study_service, tmp_path):
        # Create a study in the workspace
        workspace_path = tmp_path / "workspace1"
        study_path = workspace_path / "my_study"
        study_path.mkdir()
        (study_path / "study.antares").touch()

        with (
            patch("antarest.maintenance.tasks.watcher_scan.db"),
            patch("antarest.maintenance.tasks.watcher_scan.create_lock"),
        ):
            result = scan_workspaces(mock_config, mock_study_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.studies_found == 1
        mock_study_service.sync_studies_on_disk.assert_called_once()

    def test_dry_run_does_not_sync(self, mock_config, mock_study_service, tmp_path):
        # Create a study in the workspace
        workspace_path = tmp_path / "workspace1"
        study_path = workspace_path / "my_study"
        study_path.mkdir()
        (study_path / "study.antares").touch()

        with (
            patch("antarest.maintenance.tasks.watcher_scan.db"),
            patch("antarest.maintenance.tasks.watcher_scan.create_lock"),
        ):
            result = scan_workspaces(mock_config, mock_study_service, dry_run=True)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.studies_found == 1
        assert result.dry_run is True
        mock_study_service.sync_studies_on_disk.assert_not_called()

    def test_skips_default_workspace(self, mock_study_service, tmp_path):
        # Config with only default workspace
        config = Mock()
        config.storage = StorageConfig(
            workspaces={
                "default": WorkspaceConfig(path=tmp_path / "default"),
            }
        )

        with (
            patch("antarest.maintenance.tasks.watcher_scan.db"),
            patch("antarest.maintenance.tasks.watcher_scan.create_lock"),
        ):
            result = scan_workspaces(config, mock_study_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.studies_found == 0

    def test_returns_skipped_when_lock_not_acquired(self, mock_config, mock_study_service):
        from antarest.core.utils.lock import LockNotAcquired

        with (
            patch("antarest.maintenance.tasks.watcher_scan.db"),
            patch("antarest.maintenance.tasks.watcher_scan.create_lock", side_effect=LockNotAcquired()),
        ):
            result = scan_workspaces(mock_config, mock_study_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SKIPPED
        assert result.reason == "lock_not_acquired"

    def test_returns_error_on_exception(self, mock_config, mock_study_service):
        with patch("antarest.maintenance.tasks.watcher_scan.db", side_effect=Exception("DB error")):
            result = scan_workspaces(mock_config, mock_study_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.ERROR
        assert "DB error" in result.error


class TestWatcherScanTask:
    def test_raises_without_context(self, with_no_maintenance_ctx):
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            watcher_scan_task.run()
