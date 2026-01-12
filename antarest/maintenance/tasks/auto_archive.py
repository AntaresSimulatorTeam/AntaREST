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

"""Auto-archive task for inactive studies."""

import datetime
import logging
import time
from typing import List, NamedTuple, Optional

from pydantic import BaseModel

from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.study.model import RawStudy, Study
from antarest.study.output.output_service import OutputService
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


class ArchiveStudyResult(NamedTuple):
    archived_studies: int
    error: Optional[str] = None


class AutoArchiveTaskResult(BaseModel):
    status: BackGroundTaskStatus
    archived_studies: int
    duration_seconds: float
    dry_run: bool
    errors: List[str] = []
    reason: Optional[str] = None


class StudyToArchive(NamedTuple):
    study_id: str
    is_raw_study: bool


def _get_studies_to_archive(study_service: StudyService, threshold_days: int) -> list[StudyToArchive]:
    """Returns list of (study_id, is_raw_study) for studies inactive longer than threshold_days."""
    old_date = current_time() - datetime.timedelta(days=threshold_days)

    studies: list[Study] = list(
        study_service.repository.get_all(
            study_filter=StudyFilter(managed=True, access_permissions=AccessPermissions(is_admin=True))
        )
    )

    return [
        StudyToArchive(str(study.id), isinstance(study, RawStudy))
        for study in studies
        if (last_activity := study.last_access or study.updated_at) is not None
        and last_activity < old_date
        and (isinstance(study, VariantStudy) or not study.archived)
    ]


def _archive_study(
    study_id: str,
    is_raw_study: bool,
    study_service: StudyService,
    output_service: OutputService,
    dry_run: bool,
) -> ArchiveStudyResult:
    """Archive a study (raw) or its outputs (variant)."""
    try:
        if is_raw_study:
            logger.info(f"Archiving raw study {study_id}" + (" [dry-run]" if dry_run else ""))
            if not dry_run:
                task_id = study_service.archive(study_id)
                study_service.task_service.await_task(task_id)
        else:
            logger.info(f"Archiving variant outputs {study_id}" + (" [dry-run]" if dry_run else ""))
            if not dry_run:
                for task_id in output_service.archive_outputs(study_id):
                    study_service.task_service.await_task(task_id)
        return ArchiveStudyResult(1)
    except TaskAlreadyRunning:
        return ArchiveStudyResult(0)
    except Exception as e:
        logger.error(f"Failed to archive study {study_id}: {e}", exc_info=e)
        return ArchiveStudyResult(0, str(e))


def _clear_old_snapshots(study_service: StudyService, retention_days: int, dry_run: bool) -> None:
    """Clear variant snapshots older than retention_days."""
    logger.info(f"Clearing snapshots older than {retention_days} days" + (" [dry-run]" if dry_run else ""))
    if not dry_run:
        task_id = study_service.storage_service.variant_study_service.clear_all_snapshots(
            datetime.timedelta(days=retention_days)
        )
        study_service.task_service.await_task(task_id)


def archive_old_studies(
    study_service: StudyService,
    output_service: OutputService,
    threshold_days: int,
    snapshot_retention_days: int,
    dry_run: bool,
) -> AutoArchiveTaskResult:
    """
    Archive studies inactive for more than threshold_days and clean old snapshots.
    """
    start_time = time.time()
    archived_count = 0
    errors: list[str] = []

    logger.info(f"Starting auto-archive (dry_run={dry_run}, threshold={threshold_days}d)")

    try:
        with db():
            with create_lock(db.session, lock_id=LockId.AUTO_ARCHIVE):
                to_archive = _get_studies_to_archive(study_service, threshold_days)
                logger.info(f"Found {len(to_archive)} studies to archive")

                for study_id, is_raw in to_archive:
                    result = _archive_study(study_id, is_raw, study_service, output_service, dry_run)
                    archived_count += result.archived_studies
                    if result.error:
                        errors.append(result.error)

                _clear_old_snapshots(study_service, snapshot_retention_days, dry_run)

    except LockNotAcquired:
        logger.warning("Could not acquire lock, another auto-archive is probably running")
        return AutoArchiveTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            reason="lock_not_acquired",
            archived_studies=0,
            duration_seconds=time.time() - start_time,
            dry_run=dry_run,
        )
    except Exception as e:
        logger.error("Auto-archive failed", exc_info=e)
        return AutoArchiveTaskResult(
            status=BackGroundTaskStatus.ERROR,
            archived_studies=archived_count,
            duration_seconds=time.time() - start_time,
            dry_run=dry_run,
            errors=[str(e)],
        )

    duration = time.time() - start_time
    status = BackGroundTaskStatus.PARTIAL_SUCCESS if errors else BackGroundTaskStatus.SUCCESS
    logger.info(f"Auto-archive done in {duration:.1f}s: {archived_count} archived, {len(errors)} errors")

    return AutoArchiveTaskResult(
        status=status,
        archived_studies=archived_count,
        duration_seconds=duration,
        dry_run=dry_run,
        errors=errors,
    )
