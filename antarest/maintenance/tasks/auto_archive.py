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
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel

from antarest.core.configdata.model import ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.exceptions import OutputAlreadyArchived, TaskAlreadyRunning
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_file_lock
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.output.repository import OutputRepository
from antarest.output.service import OutputService
from antarest.study.model import RawStudy, Study
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class ArchiveStudyResult(NamedTuple):
    archived_studies: int
    error: str | None = None


class AutoArchiveTaskResult(BaseModel):
    status: BackGroundTaskStatus
    archived_studies: int
    archived_outputs: int = 0
    duration_seconds: float
    dry_run: bool
    errors: list[str] = []
    reason: str | None = None


def _get_studies_to_archive(study_service: StudyService, threshold_days: int) -> list[str]:
    """Return managed raw studies inactive longer than threshold_days."""
    old_date = current_time() - datetime.timedelta(days=threshold_days)

    studies: list[Study] = list(
        study_service.repository.get_all(
            study_filter=StudyFilter(managed=True, access_permissions=AccessPermissions(is_admin=True))
        )
    )

    return [
        study.id
        for study in studies
        if isinstance(study, RawStudy)
        and (last_activity := study.last_access or study.updated_at) is not None
        and last_activity < old_date
        and not study.archived
    ]


def _await_archive_task(task_service: ITaskService, task_id: str) -> TaskResult:
    task_service.await_task(task_id)
    task = task_service.status_task(task_id)
    if task.result is None or not task.result.success:
        raise RuntimeError(task.result.message if task.result else f"Archive task {task_id} ended without a result")
    return task.result


def _archive_old_outputs(
    study_service: StudyService, output_service: OutputService, cutoff: datetime.datetime, dry_run: bool
) -> tuple[int, set[str], list[str]]:
    repository = OutputRepository()
    archived_count = 0
    preserved_studies: set[str] = set()
    errors: list[str] = []
    studies = study_service.repository.get_all(
        StudyFilter(managed=True, archived=False, access_permissions=AccessPermissions(is_admin=True))
    )
    if not studies:
        return archived_count, preserved_studies, errors

    reference = ConfigDataRepository().get(ConfigDataAppKeys.OUTPUT_ARCHIVING_REFERENCE_DATE)
    if reference is None or reference.value is None:
        raise RuntimeError("Output archiving reference date is missing; database migrations must be applied")
    reference_date = datetime.datetime.fromisoformat(reference.value)

    for study_id in [study.id for study in studies]:
        try:
            outputs = output_service.initialize_outputs_metadata(study_id, reference_date, dry_run=dry_run)
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to inventory outputs of study %s", study_id)
            errors.append(f"{study_id}: {e}")
            preserved_studies.add(study_id)
            continue

        for output in outputs:
            if output.last_access is None or output.last_access > cutoff:
                preserved_studies.add(study_id)
                continue
            if output.archived:
                continue
            try:
                logger.info("Archiving output %s/%s%s", study_id, output.output_id, " [dry-run]" if dry_run else "")
                if dry_run:
                    archived_count += 1
                    continue
                task_id = output_service.archive_output(study_id, output.output_id, last_access_before=cutoff)
                if task_id:
                    _await_archive_task(study_service.task_service, task_id)
                    stored = repository.get(study_id, output.output_id)
                    if stored is not None and stored.archived:
                        archived_count += 1
            except (TaskAlreadyRunning, OutputAlreadyArchived):
                continue
            except Exception as e:
                db.session.rollback()
                logger.exception("Failed to archive output %s/%s", study_id, output.output_id)
                errors.append(f"{study_id}/{output.output_id}: {e}")
    return archived_count, preserved_studies, errors


def _archive_study(
    study_id: str,
    study_service: StudyService,
    output_service: OutputService,
    dry_run: bool,
    study_cutoff: datetime.datetime,
    output_cutoff: datetime.datetime,
) -> ArchiveStudyResult:
    """Archive an inactive raw study after its outputs have been handled."""
    try:
        if not dry_run and output_service.has_outputs_to_preserve(study_id, output_cutoff):
            return ArchiveStudyResult(0)
        logger.info(f"Archiving raw study {study_id}" + (" [dry-run]" if dry_run else ""))
        if not dry_run:
            task_id = study_service.archive(
                study_id, last_access_before=study_cutoff, output_last_access_before=output_cutoff
            )
            result = _await_archive_task(study_service.task_service, task_id)
            if result.return_value == "skipped":
                return ArchiveStudyResult(0)
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
    lock_folder: Path,
) -> AutoArchiveTaskResult:
    """
    Archive file outputs inactive for 60 days, then inactive studies, and clean old snapshots.
    """
    start_time = time.time()
    archived_count = 0
    archived_outputs = 0
    errors: list[str] = []
    now = current_time()
    study_cutoff = now - datetime.timedelta(days=threshold_days)
    output_cutoff = now - datetime.timedelta(days=60)

    logger.info(f"Starting auto-archive (dry_run={dry_run}, threshold={threshold_days}d)")

    try:
        with db():
            with create_file_lock(lock_id=LockId.AUTO_ARCHIVE, lock_folder=lock_folder):
                archived_outputs, preserved_studies, errors = _archive_old_outputs(
                    study_service, output_service, output_cutoff, dry_run
                )
                to_archive = _get_studies_to_archive(study_service, threshold_days)
                logger.info(f"Found {len(to_archive)} studies to archive")

                for study_id in to_archive:
                    if study_id in preserved_studies:
                        continue
                    result = _archive_study(
                        study_id, study_service, output_service, dry_run, study_cutoff, output_cutoff
                    )
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
            archived_outputs=archived_outputs,
            duration_seconds=time.time() - start_time,
            dry_run=dry_run,
            errors=[*errors, str(e)],
        )

    duration = time.time() - start_time
    status = BackGroundTaskStatus.PARTIAL_SUCCESS if errors else BackGroundTaskStatus.SUCCESS
    logger.info(
        f"Auto-archive done in {duration:.1f}s: {archived_count} studies, {archived_outputs} outputs, {len(errors)} errors"
    )

    return AutoArchiveTaskResult(
        status=status,
        archived_studies=archived_count,
        archived_outputs=archived_outputs,
        duration_seconds=duration,
        dry_run=dry_run,
        errors=errors,
    )
