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
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.launcher.model import LogType
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.repository import OutputRepository
from antarest.output.service import OutputService
from antarest.service_creator import Services
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from tests.helpers import create_raw_study, create_variant_study


def _run_concurrent_archive(
    second_side_effect: Callable[[StudyService, int], list[str]] | None = None,
) -> dict[str, AutoArchiveTaskResult]:
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

    results: dict[str, AutoArchiveTaskResult] = {}

    def slow_get_studies(study_service: StudyService, threshold_days: int) -> list[str]:
        lock_acquired.set()
        time.sleep(0.05)
        return []

    def run_first() -> None:
        with patch(
            "antarest.maintenance.tasks.auto_archive._get_studies_to_archive",
            side_effect=slow_get_studies,
        ):
            results["first"] = archive_old_studies(
                mock_study_service, mock_output_service, 60, 7, dry_run=True, lock_folder=Path(tempfile.gettempdir())
            )

    def run_second() -> None:
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
    def test_archives_old_studies_dry_run(self) -> None:
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)
        mock_output_service.has_outputs_to_preserve.return_value = False

        now = current_time()

        with db():
            repository = StudyMetadataRepository()
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
        # Variants are handled output by output, independently of study activity.
        assert result.archived_studies == 1

        # But no actual archive calls should be made
        mock_study_service.archive.assert_not_called()
        mock_output_service.archive_output.assert_not_called()

    def test_archives_inactive_outputs_of_active_study(
        self, services: Services, internal_study_id: str, tmp_path: Path
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy) and study.path is not None
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = now
            db.session.commit()
            outputs = [o for o in services.output_service.list_outputs(study.id) if not o.archived]
            output_dir = Path(study.path) / "output" / outputs[1].id

            services.output_service.initialize_outputs_metadata(study.id, now - datetime.timedelta(days=61))
            services.output_service.get_logs(study.id, outputs[0].id, LogType.STDOUT)

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)

            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == len(outputs) - 1
            assert result.archived_studies == 0
            assert (Path(study.path) / "output" / outputs[0].id).is_dir()
            assert not output_dir.exists()
            assert output_dir.with_name(output_dir.name + ".zip").is_file()

    def test_inventory_repairs_archive_status(self, services: Services, internal_study_id: str) -> None:
        last_access = current_time() - datetime.timedelta(days=90)
        with current_user_context(DEFAULT_ADMIN_USER), db():
            output_id = next(o.id for o in services.output_service.list_outputs(internal_study_id) if not o.archived)
            repository = OutputRepository()
            repository.initialize(internal_study_id, output_id, last_access, archived=True)
            repository.save_disk_usage(internal_study_id, output_id, 42)

            services.output_service.initialize_outputs_metadata(internal_study_id, current_time())

            stored = repository.get(internal_study_id, output_id)
            assert stored is not None
            assert stored.archived is False
            assert stored.last_access == last_access
            assert stored.disk_space_bytes is None

    @pytest.mark.parametrize("consult_before_maintenance", [False, True])
    def test_archives_restored_outputs_without_metadata(
        self, services: Services, internal_study_id: str, tmp_path: Path, consult_before_maintenance: bool
    ) -> None:
        now = current_time()
        reference_date = now - datetime.timedelta(days=90)
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study = services.study.get_study(internal_study_id)
                assert isinstance(study, RawStudy)
                study.workspace = DEFAULT_WORKSPACE_NAME
                study.last_access = now
                db.session.merge(
                    ConfigData(
                        owner=DEFAULT_ADMIN_USER.id,
                        key=ConfigDataAppKeys.OUTPUT_ARCHIVING_REFERENCE_DATE,
                        value=reference_date.isoformat(),
                    )
                )
                db.session.commit()
                output_ids = [o.id for o in services.output_service.list_outputs(study.id) if not o.archived]
                for output_id in output_ids:
                    OutputRepository().delete(study.id, output_id)

            # Restore a legacy study whose outputs have never been inventoried.
            for action in (services.study.archive, services.study.unarchive):
                with db():
                    task_id = action(internal_study_id)
                services.task_service.await_task(task_id)
                with db():
                    assert services.task_service.status_task(task_id).status == TaskStatus.COMPLETED

            with db():
                if consult_before_maintenance:
                    services.output_service.get_logs(internal_study_id, output_ids[0], LogType.STDOUT)
                result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
                assert result.status == BackGroundTaskStatus.SUCCESS
                assert result.archived_studies == 0
                assert result.archived_outputs == len(output_ids) - int(consult_before_maintenance)
                for output_id in output_ids:
                    stored = OutputRepository().get(internal_study_id, output_id)
                    assert stored is not None
                    if consult_before_maintenance and output_id == output_ids[0]:
                        assert stored.archived is False
                        assert stored.last_access is not None and stored.last_access >= now
                    else:
                        assert stored.archived is True
                        assert stored.last_access == reference_date

    def test_concurrent_archive_old_studies_is_skipped(self, db_middleware: None) -> None:
        results = _run_concurrent_archive()

        assert results["first"].status == BackGroundTaskStatus.SUCCESS
        assert results["second"].status == BackGroundTaskStatus.SKIPPED
        assert results["second"].reason == "lock_not_acquired"
        assert results["second"].archived_studies == 0

    def test_blocked_archive_is_not_run_after_lock_release(self, db_middleware: None) -> None:
        """Verify the second concurrent run is truly skipped, not just reported as skipped."""
        second_body_called = []

        def second_side_effect(study_service: StudyService, threshold_days: int) -> list[str]:
            second_body_called.append(True)
            return []

        results = _run_concurrent_archive(second_side_effect=second_side_effect)

        assert results["first"].status == BackGroundTaskStatus.SUCCESS
        assert results["second"].status == BackGroundTaskStatus.SKIPPED
        assert not second_body_called
