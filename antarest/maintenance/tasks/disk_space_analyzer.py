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
import logging
import time
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.study.model import StudyDiskSpaceAnalysis
from antarest.study.repository import AccessPermissions, StudyDiskSpaceRepository, StudyFilter
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class DiskSpaceAnalyzerTaskResult(BaseModel):
    status: BackGroundTaskStatus
    duration_seconds: float = 0
    updated_studies: int = 0
    reason: Optional[str] = None


def disk_space_analysis_per_study(
    repository: StudyDiskSpaceRepository, study_service: StudyService, study_id: str
) -> None:
    study_disk_analysis = repository.get(study_id)

    if not study_disk_analysis:
        study_disk_analysis = StudyDiskSpaceAnalysis(
            study_id=study_id, disk_space=study_service.get_disk_usage(study_id), last_analysis_date=datetime.now()
        )
        repository.save(study_disk_analysis)
    else:
        usage = study_service.get_disk_usage(study_id)
        repository.update(study_id, usage)


def disk_space_analysis(service: StudyService, disk_repo: StudyDiskSpaceRepository) -> DiskSpaceAnalyzerTaskResult:
    start_time = time.time()
    # we're giving admin access to the disk space analyzer due to the search_studies method
    studies = service.repository.get_all(StudyFilter(access_permissions=AccessPermissions(is_admin=True)))
    updated_studies = 0

    try:
        with db():
            with create_lock(db.session, lock_id=LockId.STUDY_DISK_SPACE):
                for study in studies:
                    if disk_repo.get(study.id) is None:
                        disk_space_analysis_per_study(disk_repo, service, study.id)
                        updated_studies += 1

    except LockNotAcquired:
        logger.info("Could not acquire lock, another disk space analysis is probably running")
        return DiskSpaceAnalyzerTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            duration_seconds=time.time() - start_time,
            updated_studies=0,
            reason="lock_not_acquired",
        )

    logger.info(f"Finished disk space analysis in {time.time() - start_time}s (updated {updated_studies} studies)")

    return DiskSpaceAnalyzerTaskResult(
        status=BackGroundTaskStatus.SUCCESS, duration_seconds=time.time() - start_time, updated_studies=updated_studies
    )
