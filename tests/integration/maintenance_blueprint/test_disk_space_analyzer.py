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

import datetime

import pytest
from antares.study.version import StudyVersion

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.maintenance.tasks.disk_space_analyzer import disk_space_analysis
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService


@pytest.fixture
def study_disk_repo() -> StudyDiskSpaceRepository:
    return StudyDiskSpaceRepository()


class TestDiskSpaceAnalyzerIntegration:
    def test_disk_space_analysis(self, study_disk_repo: StudyDiskSpaceRepository, study_service: StudyService):
        with current_user_context(DEFAULT_ADMIN_USER):
            with db():
                study_1 = study_service.create_study("my_study_1", version=StudyVersion(8, 8, 0), group_ids=[])
                study_2 = study_service.create_study("my_study_2", version=StudyVersion(8, 8, 0), group_ids=[])

            result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)
            assert result.status == BackGroundTaskStatus.SUCCESS
            assert (
                result.updated_studies == 3
            )  # there are 3 studies because one was created inside the study_service fixture before the test

            with db():
                past_analysis_date_1 = study_disk_repo.get(study_1).last_analysis_date
                past_analysis_date_2 = study_disk_repo.get(study_2).last_analysis_date

                assert study_disk_repo.get(study_1).disk_space_bytes > 0
                assert study_disk_repo.get(study_2).disk_space_bytes > 0

            result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)

            assert result.updated_studies == 0

            with db():
                recent_analysis_date_1 = study_disk_repo.get(study_1).last_analysis_date
                recent_analysis_date_2 = study_disk_repo.get(study_2).last_analysis_date
                delta_1 = datetime.datetime.now() - recent_analysis_date_1
                delta_2 = datetime.datetime.now() - recent_analysis_date_2

            assert delta_1.seconds / 60 < 1
            assert delta_2.seconds / 60 < 1

            assert recent_analysis_date_1 == past_analysis_date_1
            assert recent_analysis_date_2 == past_analysis_date_2

            # with db(): TODO : check and fix the updated_at problem (the updated_at is not updated when the study is updated)
            #     study_service.create_link(
            #         study_1, LinkCreation(name="link_1", input="input_1", output="output_1", type=Link.Type.SERIES)
            #
            #     area_1 = study_service.create_area(study_1, AreaCreation(name="fr"))
            #     area_2 = study_service.create_area(study_1, AreaCreation(name="be"))
            #
            # result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)
            #
            # assert result.updated_studies == 1

    def test_returns_skipped_when_lock_held(
        self, study_service: StudyService, study_disk_repo: StudyDiskSpaceRepository
    ):
        with db():
            with create_lock(db.session, lock_id=LockId.STUDY_DISK_SPACE):
                result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)

            assert result.status == BackGroundTaskStatus.SKIPPED
            assert result.reason == "lock_not_acquired"
