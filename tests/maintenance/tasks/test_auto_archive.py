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
from unittest.mock import Mock

import pytest

from antarest.core.exceptions import TaskAlreadyRunning
from antarest.maintenance.tasks.auto_archive import ArchiveStudyResult, _archive_study, _get_studies_to_archive
from antarest.maintenance.tasks.auto_archive_task import auto_archive_task
from antarest.study.model import RawStudy
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


def _make_study(spec, study_id, days_ago, archived=False):
    """Helper to create mock studies."""
    study = Mock(spec=spec)
    study.id = study_id
    study.last_access = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    study.updated_at = study.last_access
    if hasattr(spec, "archived"):
        study.archived = archived
    return study


class TestGetStudiesToArchive:
    def test_returns_old_raw_studies(self):
        svc = Mock()
        svc.repository.get_all.return_value = [_make_study(RawStudy, "s1", 90)]
        assert _get_studies_to_archive(svc, 60) == [("s1", True)]

    def test_returns_old_variant_studies(self):
        svc = Mock()
        svc.repository.get_all.return_value = [_make_study(VariantStudy, "v1", 90)]
        assert _get_studies_to_archive(svc, 60) == [("v1", False)]

    def test_excludes_recent_studies(self):
        svc = Mock()
        svc.repository.get_all.return_value = [_make_study(RawStudy, "s1", 30)]
        assert _get_studies_to_archive(svc, 60) == []

    def test_excludes_already_archived(self):
        svc = Mock()
        svc.repository.get_all.return_value = [_make_study(RawStudy, "s1", 90, archived=True)]
        assert _get_studies_to_archive(svc, 60) == []

    def test_uses_updated_at_when_no_last_access(self):
        svc = Mock()
        study = _make_study(RawStudy, "s1", 90)
        study.last_access = None
        svc.repository.get_all.return_value = [study]
        assert _get_studies_to_archive(svc, 60) == [("s1", True)]


class TestArchiveStudy:
    def test_archives_raw_study(self):
        study_svc, output_svc = Mock(), Mock()
        study_svc.archive.return_value = "task1"

        result = _archive_study("s1", True, study_svc, output_svc, dry_run=False)

        assert result == ArchiveStudyResult(1)
        study_svc.archive.assert_called_once_with("s1")

    def test_dry_run_does_not_archive(self):
        study_svc, output_svc = Mock(), Mock()
        result = _archive_study("s1", True, study_svc, output_svc, dry_run=True)

        assert result == ArchiveStudyResult(1)
        study_svc.archive.assert_not_called()

    def test_archives_variant_outputs(self):
        study_svc, output_svc = Mock(), Mock()
        output_svc.archive_outputs.return_value = ["t1", "t2"]

        result = _archive_study("v1", False, study_svc, output_svc, dry_run=False)

        assert result == ArchiveStudyResult(1)
        output_svc.archive_outputs.assert_called_once_with("v1")

    def test_handles_task_already_running(self):
        study_svc, output_svc = Mock(), Mock()
        study_svc.archive.side_effect = TaskAlreadyRunning()

        result = _archive_study("s1", True, study_svc, output_svc, dry_run=False)
        assert result == ArchiveStudyResult(0)

    def test_returns_error_on_exception(self):
        study_svc, output_svc = Mock(), Mock()
        study_svc.archive.side_effect = Exception("fail")

        result = _archive_study("s1", True, study_svc, output_svc, dry_run=False)
        assert result.archived_studies == 0
        assert "fail" in result.error


class TestAutoArchiveTask:
    def test_raises_without_context(self, with_no_maintenance_ctx):
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            auto_archive_task.run()
