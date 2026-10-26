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
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest_mock import MockerFixture

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.launcher.model import LogType
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.repository import OutputRepository
from antarest.service_creator import Services
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study
from antarest.study.repository import StudyFilter
from tests.helpers import create_raw_study


class TestArchiveOldStudiesIntegration:
    @pytest.mark.parametrize("initialized", [False, True])
    def test_unarchived_output_gets_a_new_grace_period(
        self, services: Services, internal_study_id: str, tmp_path: Path, initialized: bool
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study = services.study.get_study(internal_study_id)
                assert isinstance(study, RawStudy) and study.path is not None
                study.workspace = DEFAULT_WORKSPACE_NAME
                study.last_access = now - datetime.timedelta(days=90)
                db.session.commit()
                output_id = next(o.id for o in services.output_service.list_outputs(study.id) if not o.archived)
                output_dir = Path(study.path) / "output" / output_id
                repository = OutputRepository()
                repository.delete(study.id, output_id)
                if initialized:
                    repository.initialize(study.id, output_id, now - datetime.timedelta(days=90), archived=False)

            for action in (services.output_service.archive_output, services.output_service.unarchive_output):
                with db():
                    task_id = action(internal_study_id, output_id)
                assert task_id is not None
                services.task_service.await_task(task_id)
                with db():
                    assert services.task_service.status_task(task_id).status == TaskStatus.COMPLETED

            with db():
                stored = OutputRepository().get(internal_study_id, output_id)
                assert stored is not None and stored.archived is False
                assert stored.last_access is not None and stored.last_access >= now
                study = services.study.get_study(internal_study_id)
                assert study.last_access is not None and study.last_access >= now

                result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
                assert result.status == BackGroundTaskStatus.SUCCESS
                assert result.archived_outputs == result.archived_studies == 0
                assert output_dir.is_dir()
                assert not output_dir.with_name(output_dir.name + ".zip").exists()

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

            for output in outputs:
                OutputRepository().initialize(study.id, output.id, now - datetime.timedelta(days=61), output.archived)
            services.output_service.get_logs(study.id, outputs[0].id, LogType.STDOUT)

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)

            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == len(outputs) - 1
            assert result.archived_studies == 0
            assert (Path(study.path) / "output" / outputs[0].id).is_dir()
            assert not output_dir.exists()
            assert output_dir.with_name(output_dir.name + ".zip").is_file()

    @pytest.mark.parametrize("dry_run", [False, True])
    def test_inventory_repairs_archive_status(self, services: Services, internal_study_id: str, dry_run: bool) -> None:
        last_access = current_time() - datetime.timedelta(days=90)
        with current_user_context(DEFAULT_ADMIN_USER), db():
            output_id = next(o.id for o in services.output_service.list_outputs(internal_study_id) if not o.archived)
            repository = OutputRepository()
            repository.initialize(internal_study_id, output_id, last_access, archived=True)
            repository.save_disk_usage(internal_study_id, output_id, 42)

            inventory = services.output_service.initialize_outputs_metadata(internal_study_id, dry_run=dry_run)
            assert next(output for output in inventory if output.output_id == output_id).archived is False

            stored = repository.get(internal_study_id, output_id)
            assert stored is not None
            assert stored.archived is dry_run
            assert stored.last_access == last_access
            assert stored.disk_space_bytes == (42 if dry_run else None)

    def test_consultation_during_compression_cancels_archival(
        self, services: Services, internal_study_id: str, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy) and study.path is not None
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = now
            db.session.commit()
            output_id = next(o.id for o in services.output_service.list_outputs(study.id) if not o.archived)
            output_dir = Path(study.path) / "output" / output_id
            log_text = "Simulation completed successfully"
            (output_dir / "antares-out.log").write_text(log_text)
            repository = OutputRepository()
            repository.initialize(study.id, output_id, now - datetime.timedelta(days=90), archived=False)

            def compress_and_read(src: Path, target: Path, *, archive_format: ArchiveFormat) -> None:
                archive_dir(src, target, archive_format=archive_format)
                # A separate session records a consultation after the task's initial eligibility check.
                with db():
                    assert services.output_service.get_logs(study.id, output_id, LogType.STDOUT) == log_text

            mocker.patch("antarest.output.storage.file.abstract_storage.archive_dir", side_effect=compress_and_read)

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)

            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == result.archived_studies == 0
            stored = repository.get(study.id, output_id)
            assert stored is not None and stored.archived is False
            assert stored.last_access is not None and stored.last_access >= now
            assert (output_dir / "antares-out.log").read_text() == log_text
            assert not output_dir.with_name(output_dir.name + ".zip").exists()
            assert not list(output_dir.parent.glob("~archive-*.tmp"))

    def test_inventory_failure_does_not_stop_other_studies(
        self, services: Services, internal_study_id: str, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        now = current_time()
        clear_snapshots = mocker.spy(services.study.storage_service.variant_study_service, "clear_all_snapshots")
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy)
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = now
            broken_path = tmp_path / "broken"
            parameters = broken_path / "output" / "20260101-0000eco" / "about-the-study" / "parameters.ini"
            parameters.parent.mkdir(parents=True)
            parameters.write_text("[general]\nnbyears = 1\nyear-by-year = true\n[output]\n")
            broken = create_raw_study(
                id="broken",
                path=str(broken_path),
                workspace=DEFAULT_WORKSPACE_NAME,
                last_access=now,
            )
            db.session.add(broken)
            db.session.commit()
            for output in services.output_service.list_outputs(study.id):
                OutputRepository().initialize(study.id, output.id, now - datetime.timedelta(days=90), output.archived)
            output_count = sum(not output.archived for output in services.output_service.list_outputs(study.id))

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)

            assert result.status == BackGroundTaskStatus.PARTIAL_SUCCESS
            assert result.archived_outputs == output_count > 0
            assert len(result.errors) == 1 and "broken" in result.errors[0]
            assert services.study.get_study(broken.id).archived is False
            clear_snapshots.assert_called_once()

    @pytest.mark.parametrize("initialized", [False, True])
    def test_dry_run_matches_archival_without_writing_metadata(
        self, services: Services, internal_study_id: str, tmp_path: Path, initialized: bool, mocker: MockerFixture
    ) -> None:
        archive_output = mocker.spy(services.output_service, "archive_output")
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy)
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = now - datetime.timedelta(days=90)
            db.session.commit()
            outputs = list(services.output_service.list_outputs(study.id))
            repository = OutputRepository()
            for output in outputs:
                repository.delete(study.id, output.id)
            if initialized:
                for output in outputs:
                    repository.initialize(study.id, output.id, now - datetime.timedelta(days=90), output.archived)

            preview = archive_old_studies(services.study, services.output_service, 60, 7, True, tmp_path)
            for output in outputs:
                stored = repository.get(study.id, output.id)
                if initialized:
                    assert stored is not None and stored.archived == output.archived
                    assert stored.last_access == now - datetime.timedelta(days=90)
                else:
                    assert stored is None
            assert list(services.output_service.list_outputs(study.id)) == outputs
            assert services.study.get_study(study.id).archived is False

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
            assert preview.status == result.status == BackGroundTaskStatus.SUCCESS
            assert preview.archived_studies == result.archived_studies == 1
            assert preview.archived_outputs == result.archived_outputs == 0
            archive_output.assert_not_called()

    def test_restored_outputs_without_metadata_get_a_new_grace_period(
        self, services: Services, internal_study_id: str, tmp_path: Path
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study = services.study.get_study(internal_study_id)
                assert isinstance(study, RawStudy)
                study.workspace = DEFAULT_WORKSPACE_NAME
                study.last_access = now
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
                result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
                assert result.status == BackGroundTaskStatus.SUCCESS
                assert result.archived_studies == 0
                assert result.archived_outputs == 0
                for output_id in output_ids:
                    stored = OutputRepository().get(internal_study_id, output_id)
                    assert stored is not None
                    assert stored.archived is False
                    assert stored.last_access is not None and stored.last_access >= now

    def test_concurrent_archive_is_skipped_without_running_after_lock_release(
        self, db_middleware: None, tmp_path: Path
    ) -> None:
        lock_acquired, release_lock = threading.Event(), threading.Event()
        study_service, output_service = Mock(), Mock()
        study_service.repository.get_all.return_value = []
        results: list[AutoArchiveTaskResult] = []

        def hold_lock(study_filter: StudyFilter) -> list[Study]:
            lock_acquired.set()
            assert release_lock.wait(timeout=5)
            return []

        def run_first() -> None:
            results.append(archive_old_studies(study_service, output_service, 60, 7, True, tmp_path))

        with patch.object(study_service.repository, "get_all", side_effect=hold_lock) as body:
            first = threading.Thread(target=run_first)
            first.start()
            try:
                assert lock_acquired.wait(timeout=5)
                second = archive_old_studies(study_service, output_service, 60, 7, True, tmp_path)
            finally:
                release_lock.set()
                first.join(timeout=5)
            assert not first.is_alive()
            body.assert_called_once()

        assert results[0].status == BackGroundTaskStatus.SUCCESS
        assert second.status == BackGroundTaskStatus.SKIPPED
        assert second.reason == "lock_not_acquired"
        assert second.archived_studies == second.archived_outputs == 0
