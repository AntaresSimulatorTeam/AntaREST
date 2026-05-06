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
from typing import Optional

from pydantic import BaseModel

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.core.utils.utils import current_time
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
    error: Optional[str] = None


def disk_space_analysis(service: StudyService, disk_repo: StudyDiskSpaceRepository) -> DiskSpaceAnalyzerTaskResult:
    start_time = time.time()

    updated_studies = 0

    try:
        with db():
            with create_lock(db.session, lock_id=LockId.STUDY_DISK_SPACE):
                # we're giving admin access to the disk space analyzer due to the search_studies method
                studies = service.repository.get_all(StudyFilter(access_permissions=AccessPermissions(is_admin=True), managed=True))
                disk_analysis = disk_repo.get_all()

                dict_analysis = {element.study_id: element for element in disk_analysis}

                for study in studies:
                    updated_at = study.updated_at
                    try:
                        filtered_analysis = dict_analysis.get(study.id, None)

                        if not filtered_analysis:
                            logger.info(f"Creating a disk space analysis for study {study.id}")
                            study_disk_analysis = StudyDiskSpaceAnalysis(
                                study_id=study.id,
                                disk_space_bytes=service.get_disk_usage(study.id),
                                last_analysis_date=current_time(),
                            )
                            disk_repo.save(study_disk_analysis)
                            updated_studies += 1

                        elif updated_at is not None and (filtered_analysis.last_analysis_date < updated_at):
                            logger.info(f"Updating disk space analysis for study {study.id}")

                            usage = service.get_disk_usage(study.id)
                            disk_repo.update(study.id, usage)
                            updated_studies += 1

                    except Exception as e:
                        logger.error(f"Failed to analyze disk space for study {study.id}: {e}", exc_info=e)

    except LockNotAcquired:
        logger.info("Could not acquire lock, another disk space analysis is probably running")
        return DiskSpaceAnalyzerTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            duration_seconds=time.time() - start_time,
            updated_studies=0,
            reason="lock_not_acquired",
        )
    except Exception as e:
        logger.error("Disk space analysis failed", exc_info=e)
        return DiskSpaceAnalyzerTaskResult(
            status=BackGroundTaskStatus.ERROR,
            duration_seconds=time.time() - start_time,
            updated_studies=0,
            error=str(e),
        )

    logger.info(f"Finished disk space analysis in {time.time() - start_time}s (updated {updated_studies} studies)")

    return DiskSpaceAnalyzerTaskResult(
        status=BackGroundTaskStatus.SUCCESS, duration_seconds=time.time() - start_time, updated_studies=updated_studies
    )
