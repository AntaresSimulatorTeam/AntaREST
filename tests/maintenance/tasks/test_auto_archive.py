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

"""Tests for auto-archive task."""

import datetime
from unittest.mock import Mock, call

import pytest

from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.tasks.model import TaskResult
from antarest.maintenance.tasks.auto_archive import (
    ArchiveStudyResult,
    _archive_inactive_studies_and_outputs,
    _archive_study,
)
from antarest.maintenance.tasks.auto_archive_task import auto_archive_task
from antarest.study.model import RawStudy, Study
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

CUTOFF = datetime.datetime(2026, 1, 1)


def _make_study(spec: type[Study], study_id: str, days_ago: int, archived: bool = False) -> Study:
    """Helper to create mock studies."""
    study = Mock(spec=spec)
    study.id = study_id
    study.last_access = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    study.updated_at = study.last_access
    if hasattr(spec, "archived"):
        study.archived = archived
    return study


def test_selects_inactive_raw_studies_in_a_single_pass() -> None:
    svc = Mock()
    without_last_access = _make_study(RawStudy, "fallback", 90)
    without_last_access.last_access = None
    svc.repository.get_all.return_value = [
        _make_study(RawStudy, "old", 90),
        _make_study(VariantStudy, "variant", 90),
        _make_study(RawStudy, "recent", 30),
        without_last_access,
    ]
    outputs = Mock()
    outputs.initialize_outputs_metadata.return_value = []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=60)

    assert _archive_inactive_studies_and_outputs(svc, outputs, cutoff, True) == (2, 0, [])
    svc.repository.get_all.assert_called_once()
    assert outputs.initialize_outputs_metadata.call_args_list == [
        call("variant", dry_run=True),
        call("recent", dry_run=True),
    ]


class TestArchiveStudy:
    def test_handles_task_already_running(self) -> None:
        study_svc = Mock()
        study_svc.archive.side_effect = TaskAlreadyRunning()

        result = _archive_study("s1", study_svc, False, CUTOFF)
        assert result == ArchiveStudyResult(0)

    def test_returns_error_on_exception(self) -> None:
        study_svc = Mock()
        study_svc.archive.return_value = "task1"
        study_svc.task_service.status_task.return_value.result = TaskResult(success=False, message="fail")

        result = _archive_study("s1", study_svc, False, CUTOFF)
        assert result.archived_studies == 0
        assert result.error is not None
        assert "fail" in result.error


class TestAutoArchiveTask:
    def test_raises_without_context(self, with_no_maintenance_ctx: None) -> None:
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            auto_archive_task.run()
