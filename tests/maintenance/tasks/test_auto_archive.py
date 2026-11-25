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
from tests.helpers import with_db_context

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


@with_db_context
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
    outputs.get_outputs_to_archive.return_value = []
    outputs.list_outputs.return_value = []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=60)

    result = _archive_inactive_studies_and_outputs(svc, outputs, cutoff, True)
    assert result.archived_studies == 2
    assert result.archived_outputs == 0
    assert result.errors == []
    svc.repository.get_all.assert_called_once()
    assert outputs.get_outputs_to_archive.call_args_list == [call("variant", cutoff), call("recent", cutoff)]
    outputs.list_outputs.assert_not_called()


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("inactive", [False, True])
@pytest.mark.parametrize("has_last_access", [False, True])
@with_db_context
def test_variant_outputs_use_the_same_cutoff_regardless_of_study_activity(
    dry_run: bool, inactive: bool, has_last_access: bool
) -> None:
    study = _make_study(VariantStudy, "variant", 90 if inactive else 30)
    if not has_last_access:
        study.last_access = None
    study_service, output_service = Mock(), Mock()
    study_service.repository.get_all.return_value = [study]
    study_service.task_service.status_task.return_value.result = TaskResult(success=True, message="ok")
    output_service.get_outputs_to_archive.return_value = ["old-output"]
    cutoff = datetime.datetime.now() - datetime.timedelta(days=60)

    result = _archive_inactive_studies_and_outputs(study_service, output_service, cutoff, dry_run)

    assert result.archived_studies == 0
    assert result.archived_outputs == 1
    assert result.errors == []
    study_service.archive.assert_not_called()
    output_service.list_outputs.assert_not_called()
    output_service.get_outputs_to_archive.assert_called_once_with("variant", cutoff)
    if not dry_run:
        output_service.archive_output.assert_called_once_with("variant", "old-output", archive_before=cutoff)
        study_service.task_service.await_task.assert_called_once()
    else:
        output_service.archive_output.assert_not_called()


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
