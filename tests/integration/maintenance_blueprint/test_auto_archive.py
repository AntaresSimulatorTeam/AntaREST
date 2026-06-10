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

"""Integration tests for the auto-archive task."""

import datetime
import tempfile
import threading
import time
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.service import OutputService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from tests.helpers import create_raw_study, create_variant_study


def _run_concurrent_archive(second_side_effect=None) -> dict:
    """Run archive_old_studies in two threads concurrently.

    The first thread holds the file lock while executing; the second thread
    attempts to acquire the same lock while it is held.

    Returns a dict with keys "first" and "second" containing the task results.
    """
    lock_acquired = threading.Event()

    mock_study_service = Mock()
    mock_output_service = Mock()
    mock_study_service.repository.get_all.return_value = []
    mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0
    mock_study_service.task_service = Mock()

    results = {}

    def slow_get_studies(*args, **kwargs):
        lock_acquired.set()
        time.sleep(0.05)
        return []

    def run_first():
        with patch(
            "antarest.maintenance.tasks.auto_archive._get_studies_to_archive",
            side_effect=slow_get_studies,
        ):
            results["first"] = archive_old_studies(
                mock_study_service, mock_output_service, 60, 7, dry_run=True, lock_folder=Path(tempfile.gettempdir())
            )

    def run_second():
        lock_acquired.wait(timeout=2)
        ctx = (
            patch(
                "antarest.maintenance.tasks.auto_archive._get_studies_to_archive",
                side_effect=second_side_effect,
            )
            if second_side_effect is not None
            else nullcontext()
        )
        with ctx:
            results["second"] = archive_old_studies(
                mock_study_service, mock_output_service, 60, 7, dry_run=True, lock_folder=Path(tempfile.gettempdir())
            )

    t1 = threading.Thread(target=run_first)
    t2 = threading.Thread(target=run_second)
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)

    return results


class TestArchiveOldStudiesIntegration:
    def test_archives_old_studies_dry_run(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create old studies that should be archived
            db_session.add_all(
                [
                    create_raw_study(
                        id="old_raw",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=90),
                        archived=False,
                    ),
                    create_variant_study(
                        id="old_variant",
                        updated_at=now - datetime.timedelta(days=90),
                    ),
                    create_raw_study(
                        id="recent_raw",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=30),
                        archived=False,
                    ),
                ]
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=True,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.dry_run is True
        # In dry_run, we still count what would be archived (old_raw + old_variant)
        assert result.archived_studies == 2

        # But no actual archive calls should be made
        mock_study_service.archive.assert_not_called()
        mock_output_service.archive_outputs.assert_not_called()

    def test_returns_success_with_no_old_studies(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create only recent studies
            db_session.add_all(
                [
                    create_raw_study(
                        id="recent1",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=30),
                        archived=False,
                    ),
                    create_raw_study(
                        id="recent2",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=10),
                        archived=False,
                    ),
                ]
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = "snapshot_task"
            mock_study_service.task_service = Mock()

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=False,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.archived_studies == 0
        mock_study_service.task_service.await_task.assert_called_once_with("snapshot_task")
        assert result.duration_seconds >= 0

    def test_excludes_already_archived_studies(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create an old but already archived study
            db_session.add(
                create_raw_study(
                    id="already_archived",
                    workspace=DEFAULT_WORKSPACE_NAME,
                    updated_at=now - datetime.timedelta(days=90),
                    archived=True,
                ),
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=True,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.archived_studies == 0

    def test_concurrent_archive_old_studies_is_skipped(self, db_middleware):
        results = _run_concurrent_archive()

        assert results["first"].status == BackGroundTaskStatus.SUCCESS
        assert results["second"].status == BackGroundTaskStatus.SKIPPED
        assert results["second"].reason == "lock_not_acquired"
        assert results["second"].archived_studies == 0

    def test_blocked_archive_is_not_run_after_lock_release(self, db_middleware):
        """Verify the second concurrent run is truly skipped, not just reported as skipped."""
        second_body_called = []

        def second_side_effect(*args, **kwargs):
            second_body_called.append(True)
            return []

        results = _run_concurrent_archive(second_side_effect=second_side_effect)

        assert results["first"].status == BackGroundTaskStatus.SUCCESS
        assert results["second"].status == BackGroundTaskStatus.SKIPPED
        assert not second_body_called
