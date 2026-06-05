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

"""Tests for tasks GC task."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.maintenance.tasks.gc_tasks import clean_tasks
from antarest.maintenance.tasks.gc_tasks_task import gc_tasks_task


class TestCleanTasks:
    def test_clean_tasks_when_not_dry_run(self):
        mock_service = Mock()
        mock_service.delete_task_by_creation_date.return_value = 5
        gc_tasks_result = clean_tasks(
            mock_service, dry_run=False, task_retention_duration=60, lock_folder=Path(tempfile.gettempdir())
        )
        mock_service.delete_task_by_creation_date.assert_called_once_with(60)
        assert gc_tasks_result.status == "success"
        assert gc_tasks_result.deleted_count == 5
        assert gc_tasks_result.error is None

    def test_does_not_clean_tasks_when_dry_run(self):
        mock_service = Mock()
        mock_service.delete_task_by_creation_date.return_value = 5
        gc_tasks_result = clean_tasks(
            mock_service, dry_run=True, task_retention_duration=60, lock_folder=Path(tempfile.gettempdir())
        )
        mock_service.delete_task_by_creation_date.assert_not_called()
        assert gc_tasks_result.deleted_count == 0
        assert gc_tasks_result.error is None


class TestTasksGCTask:
    def test_raises_without_context(self, with_no_maintenance_ctx):
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            gc_tasks_task.run()
