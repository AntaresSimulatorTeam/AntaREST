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

"""Integration tests for the disk space analyzer."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from antares.study.version import StudyVersion

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_file_lock
from antarest.core.utils.utils import current_time
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.maintenance.tasks.disk_space_analyzer import disk_space_analysis
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService
from antarest.study.storage.utils import is_managed


@pytest.fixture
def study_disk_repo() -> StudyDiskSpaceRepository:
    return StudyDiskSpaceRepository()


@pytest.fixture(autouse=True)
def strictly_increasing_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each call to `current_time` returns a later date, so strict date comparisons never depend on the clock resolution."""
    start = current_time()
    calls = iter(range(1, 10_000))

    def fake_current_time() -> datetime:
        return start + timedelta(seconds=next(calls))

    monkeypatch.setattr("antarest.maintenance.tasks.disk_space_analyzer.current_time", fake_current_time)
    monkeypatch.setattr("antarest.study.repository.current_time", fake_current_time)


class TestDiskSpaceAnalyzerIntegration:
    def test_disk_space_analysis(
        self, study_disk_repo: StudyDiskSpaceRepository, study_service: StudyService, task_service: ITaskService
    ) -> None:
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study_1 = study_service.create_study("my_study_1", version=StudyVersion(8, 8, 0), group_ids=[])
                study_2 = study_service.create_study("my_study_2", version=StudyVersion(8, 8, 0), group_ids=[])

            result = disk_space_analysis(
                service=study_service,
                disk_repo=study_disk_repo,
                lock_folder=Path(tempfile.gettempdir()),
            )
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert (
                result.updated_studies == 2
            )  # there are 2 managed studies because one was created inside the study_service fixture before the test
            with db():
                assert is_managed(study_service.get_study(study_1))
                assert is_managed(study_service.get_study(study_2))

            with db():
                analysis_1 = study_disk_repo.get(study_1)
                assert analysis_1 is not None
                past_analysis_date_1 = analysis_1.last_analysis_date
                analysis_2 = study_disk_repo.get(study_2)
                assert analysis_2 is not None
                past_analysis_date_2 = analysis_2.last_analysis_date

                assert analysis_1.disk_space_bytes > 0
                assert analysis_2.disk_space_bytes > 0

            result = disk_space_analysis(
                service=study_service,
                disk_repo=study_disk_repo,
                lock_folder=Path(tempfile.gettempdir()),
            )

            assert result.updated_studies == 0

            with db():
                analysis_1 = study_disk_repo.get(study_1)
                assert analysis_1 is not None
                past_disk_space = analysis_1.disk_space_bytes
                recent_analysis_date_1 = analysis_1.last_analysis_date
                analysis_2 = study_disk_repo.get(study_2)
                assert analysis_2 is not None
                recent_analysis_date_2 = analysis_2.last_analysis_date

            assert recent_analysis_date_1 == past_analysis_date_1
            assert recent_analysis_date_2 == past_analysis_date_2

            with db():
                archive_task_id = study_service.archive(study_1)
            # Archiving runs in a task: wait for its completion before analyzing
            task_service.await_task(archive_task_id)

            result = disk_space_analysis(
                service=study_service,
                disk_repo=study_disk_repo,
                lock_folder=Path(tempfile.gettempdir()),
            )

            with db():
                analysis_1 = study_disk_repo.get(study_1)
                assert analysis_1 is not None
                current_disk_space = analysis_1.disk_space_bytes
                last_analysis_date = analysis_1.last_analysis_date

            assert current_disk_space < past_disk_space
            assert recent_analysis_date_1 < last_analysis_date

            assert result.updated_studies == 1

    def test_invalidated_study_is_analyzed_again(
        self, study_disk_repo: StudyDiskSpaceRepository, study_service: StudyService
    ) -> None:
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study_id = study_service.create_study("my_study", version=StudyVersion(8, 8, 0), group_ids=[])

            def analyze() -> int:
                return disk_space_analysis(
                    service=study_service, disk_repo=study_disk_repo, lock_folder=Path(tempfile.gettempdir())
                ).updated_studies

            assert analyze() >= 1
            assert analyze() == 0

            # A change on the disk space which doesn't update the study (e.g. output deletion)
            with db():
                study_service.invalidate_disk_space(study_id)

            assert analyze() == 1
            assert analyze() == 0

    def test_invalidation_during_analysis_is_not_lost(
        self,
        study_disk_repo: StudyDiskSpaceRepository,
        study_service: StudyService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study_id = study_service.create_study("my_study", version=StudyVersion(8, 8, 0), group_ids=[])

            def analyze() -> int:
                return disk_space_analysis(
                    service=study_service, disk_repo=study_disk_repo, lock_folder=Path(tempfile.gettempdir())
                ).updated_studies

            assert analyze() >= 1

            with db():
                study_service.invalidate_disk_space(study_id)

            # The study is invalidated again while its disk space is being measured
            real_get_disk_usage = study_service.get_disk_usage

            def get_disk_usage_and_invalidate(uuid: str) -> int:
                usage = real_get_disk_usage(uuid)
                study_service.invalidate_disk_space(uuid)
                return usage

            with monkeypatch.context() as ctx:
                ctx.setattr(study_service, "get_disk_usage", get_disk_usage_and_invalidate)
                assert analyze() == 1

            # The last invalidation happened after the analysis started: it must be analyzed again
            assert analyze() == 1
            assert analyze() == 0

    def test_returns_skipped_when_lock_held(
        self, study_service: StudyService, study_disk_repo: StudyDiskSpaceRepository
    ) -> None:
        lock_folder = Path(tempfile.gettempdir())
        with db():
            with create_file_lock(lock_id=LockId.STUDY_DISK_SPACE, lock_folder=lock_folder):
                result = disk_space_analysis(
                    service=study_service,
                    disk_repo=study_disk_repo,
                    lock_folder=lock_folder,
                )

            assert result.status == BackGroundTaskStatus.SKIPPED
            assert result.reason == "lock_not_acquired"
