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
from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.launcher.model import LogType
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.repository import OutputRepository
from antarest.output.storage.output_storage import OutputStorageType
from antarest.service_creator import Services
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study
from antarest.study.repository import StudyFilter
from tests.helpers import create_raw_study
from tests.integration.utils import wait_task_completion


class TestArchiveOldStudiesIntegration:
    def test_unarchiving_study_renews_restored_outputs_grace_period(
        self, admin_client: TestClient, services: Services, output_zip: Path, tmp_path: Path
    ) -> None:
        response = admin_client.post("/v1/studies", params={"name": "Study to restore"})
        assert response.status_code == 201, response.text
        study_id = response.json()
        with current_user_context(DEFAULT_ADMIN_USER), db(), output_zip.open("rb") as output_file:
            output_id = services.output_service.import_output(
                study_id, output_file, storage_type=OutputStorageType.IN_STUDY_FILE_TREE
            )
            services.study.get_study(study_id).last_access = current_time() - datetime.timedelta(days=90)
            db.session.commit()

        for action in ("archive", "unarchive"):
            response = admin_client.put(f"/v1/studies/{study_id}/{action}")
            assert response.status_code == 200, response.text
            assert wait_task_completion(admin_client, None, response.json()).status == TaskStatus.COMPLETED

        # No study GET before maintenance: restoration itself must renew the grace period.
        with current_user_context(DEFAULT_ADMIN_USER):
            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_studies == result.archived_outputs == 0
            with db():
                output = next(o for o in services.output_service.list_outputs(study_id) if o.id == output_id)
                assert not output.archived

    @pytest.mark.parametrize("storage_type", [OutputStorageType.OUT_OF_STUDY_FILE_TREE, OutputStorageType.V2])
    @pytest.mark.parametrize("dry_run", [False, True])
    def test_inactive_variant_rearchives_recently_unarchived_outputs(
        self,
        admin_client: TestClient,
        services: Services,
        output_zip: Path,
        tmp_path: Path,
        storage_type: OutputStorageType,
        dry_run: bool,
    ) -> None:
        response = admin_client.post("/v1/studies", params={"name": "Parent study"})
        assert response.status_code == 201, response.text
        parent_id = response.json()
        response = admin_client.post(f"/v1/studies/{parent_id}/variants", params={"name": "Inactive variant"})
        assert response.status_code == 200, response.text
        variant_id = response.json()
        with current_user_context(DEFAULT_ADMIN_USER):
            with db(), output_zip.open("rb") as output_file:
                output_id = services.output_service.import_output(variant_id, output_file, storage_type=storage_type)
            assert output_id is not None
            for action in (services.output_service.archive_output, services.output_service.unarchive_output):
                with db():
                    task_id = action(variant_id, output_id)
                assert task_id is not None
                services.task_service.await_task(task_id)
                with db():
                    assert services.task_service.status_task(task_id).status == TaskStatus.COMPLETED

            now = current_time()
            with db():
                variant = services.study.get_study(variant_id)
                variant.last_access = now - datetime.timedelta(days=90)
                db.session.commit()
                stored = OutputRepository().get(variant_id, output_id)
                assert stored is not None and stored.last_unarchiving_date is not None
                assert stored.last_unarchiving_date > now - datetime.timedelta(days=1)

            result = archive_old_studies(services.study, services.output_service, 60, 7, dry_run, tmp_path)

            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs >= 1
            with db():
                output = next(o for o in services.output_service.list_outputs(variant_id) if o.id == output_id)
                assert output.archived is not dry_run

    def test_unarchived_output_gets_a_new_grace_period(self, services: Services, internal_study_id: str) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study = services.study.get_study(internal_study_id)
                assert isinstance(study, RawStudy)
                study.workspace = DEFAULT_WORKSPACE_NAME
                db.session.commit()
                output_id = next(
                    o.id for o in services.output_service.list_outputs(internal_study_id) if not o.archived
                )
                # A cached size must not prevent recording the unarchiving date.
                services.output_service.get_disk_usage(internal_study_id, output_id)

            for action in (services.output_service.archive_output, services.output_service.unarchive_output):
                with db():
                    task_id = action(internal_study_id, output_id)
                assert task_id is not None
                services.task_service.await_task(task_id)
                with db():
                    assert services.task_service.status_task(task_id).status == TaskStatus.COMPLETED

            with db():
                stored = OutputRepository().get(internal_study_id, output_id)
                assert stored is not None
                assert stored.last_unarchiving_date is not None and stored.last_unarchiving_date >= now
                assert stored.disk_space_bytes is None
                assert output_id not in services.output_service.get_outputs_to_archive(
                    internal_study_id, now - datetime.timedelta(days=60)
                )

    @pytest.mark.parametrize("dry_run", [False, True])
    def test_outputs_are_archived_only_after_the_grace_period(
        self, services: Services, internal_study_id: str, tmp_path: Path, dry_run: bool
    ) -> None:
        now = current_time()
        with current_user_context(DEFAULT_ADMIN_USER), db():
            study = services.study.get_study(internal_study_id)
            assert isinstance(study, RawStudy) and study.path is not None
            study.workspace = DEFAULT_WORKSPACE_NAME
            study.last_access = now
            db.session.commit()
            outputs = [o for o in services.output_service.list_outputs(study.id) if not o.archived]
            for output in outputs:
                OutputRepository().delete(study.id, output.id)

            result = archive_old_studies(services.study, services.output_service, 60, 7, dry_run, tmp_path)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == 0
            if dry_run:
                assert OutputRepository().get_all(study.id) == []
            assert services.output_service.get_outputs_to_archive(study.id, now) == []
            for output in outputs:
                stored = OutputRepository().get(study.id, output.id)
                assert stored is not None and stored.last_unarchiving_date is not None
                assert stored.last_unarchiving_date >= now
                # Simulate expiration of the grace period.
                OutputRepository().save_unarchiving_date(study.id, output.id, now - datetime.timedelta(days=61))
            services.output_service.get_logs(study.id, outputs[0].id, LogType.STDOUT)

            result = archive_old_studies(services.study, services.output_service, 60, 7, dry_run, tmp_path)

            assert result.status == BackGroundTaskStatus.SUCCESS
            assert result.archived_outputs == len(outputs) > 0
            assert result.archived_studies == 0
            for output in outputs:
                output_dir = Path(study.path) / "output" / output.id
                assert output_dir.is_dir() is dry_run
                assert output_dir.with_name(output_dir.name + ".zip").is_file() is not dry_run

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
            outputs = [o for o in services.output_service.list_outputs(study.id) if not o.archived]
            for output in outputs:
                OutputRepository().save_unarchiving_date(study.id, output.id, now - datetime.timedelta(days=61))

            result = archive_old_studies(services.study, services.output_service, 60, 7, False, tmp_path)

            assert result.status == BackGroundTaskStatus.PARTIAL_SUCCESS
            assert result.archived_outputs == len(outputs)
            assert len(result.errors) == 1 and "broken" in result.errors[0]
            assert services.study.get_study(broken.id).archived is False
            clear_snapshots.assert_called_once()

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
