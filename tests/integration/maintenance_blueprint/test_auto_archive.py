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
import zipfile
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from pytest_mock import MockerFixture

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.jwt import DEFAULT_ADMIN_USER
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
        mock_output_service.archive_outputs.assert_not_called()

    def test_archives_inactive_outputs_of_active_study(
        self, services: Services, internal_study_id: str, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy) and study.path is not None
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = study.updated_at = now - datetime.timedelta(days=90)
            db.session.add(
                ConfigData(
                    owner=DEFAULT_ADMIN_USER.id,
                    key=ConfigDataAppKeys.OUTPUT_ARCHIVING_REFERENCE_DATE,
                    value=now.isoformat(),
                )
            )
            db.session.commit()
            outputs = [o for o in services.output_service.list_outputs(study.id) if not o.archived]
            output_dir = Path(study.path) / "output" / outputs[1].id
            parameters = (output_dir / "about-the-study" / "parameters.ini").read_bytes()
            original_size = sum(p.stat().st_size for p in output_dir.rglob("*") if p.is_file())

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == result.archived_studies == 0

            future = now + datetime.timedelta(days=61)
            mocker.patch("antarest.maintenance.tasks.auto_archive.current_time", return_value=future)
            mocker.patch("antarest.output.service.current_time", return_value=future)
            services.output_service.get_logs(study.id, outputs[0].id, LogType.STDOUT)
            preview = archive_old_studies(services.study, services.output_service, 60, 7, True, tmp_path)
            assert preview.archived_outputs == len(outputs) - 1
            assert output_dir.is_dir()

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == len(outputs) - 1
            assert result.archived_studies == 0
            task_id = services.study.archive(study.id, last_access_before=future - datetime.timedelta(days=60))
            services.task_service.await_task(task_id)
            task = services.task_service.status_task(task_id)
            assert task.result is not None and task.result.return_value == "skipped"
            stored = OutputRepository().get(study.id, outputs[1].id)
            assert stored is not None and stored.archived and stored.last_access == now
            assert (Path(study.path) / "output" / outputs[0].id).is_dir()
            assert not output_dir.exists()
            archive = output_dir.with_name(output_dir.name + ".zip")
            assert archive.stat().st_size < original_size
            with zipfile.ZipFile(archive) as zipped:
                assert zipped.read("about-the-study/parameters.ini") == parameters

    def test_excludes_already_archived_studies(self) -> None:
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository()
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
