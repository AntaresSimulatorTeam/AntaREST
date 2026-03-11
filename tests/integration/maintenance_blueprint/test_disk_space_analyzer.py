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
import pytest

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.maintenance.tasks.common import LockId, BackGroundTaskStatus
from antarest.maintenance.tasks.disk_space_analyzer import disk_space_analysis
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService

@pytest.fixture
def study_disk_repo() -> StudyDiskSpaceRepository:
    return StudyDiskSpaceRepository()

class TestDiskSpaceAnalyzerIntegration:

    def test_disk_space_analyzer(self):
        pass

    def test_returns_skipped_when_lock_held(self, study_service: StudyService, study_disk_repo: StudyDiskSpaceRepository):
        with db():
            with create_lock(db.session, lock_id=LockId.STUDY_DISK_SPACE):
                result = disk_space_analysis(service=study_service, disk_repo=study_disk_repo)

            assert result.status == BackGroundTaskStatus.SKIPPED
            assert result.reason == "lock_not_acquired"