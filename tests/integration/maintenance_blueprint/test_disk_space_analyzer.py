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

from datetime import datetime, timedelta, timezone

import pytest

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.maintenance.tasks.disk_space_analyzer import disk_space_analysis
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService
from tests.helpers import create_study, with_db_context


@pytest.fixture
def study_disk_repo() -> StudyDiskSpaceRepository:
    return StudyDiskSpaceRepository()


class TestDiskSpaceAnalyzerIntegration:
    # @with_admin_user
    # @with_db_context
    def test_martin(self, study_disk_repo: StudyDiskSpaceRepository, study_service: StudyService):
        with current_user_context(DEFAULT_ADMIN_USER):
            print("oj")

    # @with_admin_user
    @with_db_context
    def test_disk_space_analysis(self, study_disk_repo: StudyDiskSpaceRepository, study_service: StudyService):
        with current_user_context(DEFAULT_ADMIN_USER):
            past_date = datetime.now(timezone.utc) - timedelta(hours=1)
            study_1 = create_study(name="my_study_1", updated_at=past_date)
            study_2 = create_study(name="my_study_2", updated_at=past_date)

            db.session.add(study_1)
            db.session.commit()
            db.session.add(study_2)
            db.session.commit()
            result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert (
                result.updated_studies == 3
            )  # there are 3 studies because one was created inside the study_service fixture before the test

    def test_returns_skipped_when_lock_held(
        self, study_service: StudyService, study_disk_repo: StudyDiskSpaceRepository
    ):
        with db():
            with create_lock(db.session, lock_id=LockId.STUDY_DISK_SPACE):
                result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)

            assert result.status == BackGroundTaskStatus.SKIPPED
            assert result.reason == "lock_not_acquired"
