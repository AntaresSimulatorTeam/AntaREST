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

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.exceptions import OutputAlreadyArchived, TaskAlreadyRunning
from antarest.core.jwt import DEFAULT_ADMIN_USER
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


def _initialize_outputs_metadata(study_service: StudyService, output_service: OutputService) -> None:
    """Inventory existing outputs once, under the auto-archive lock and DB session."""
    repository = ConfigDataRepository()
    if repository.get(ConfigDataAppKeys.OUTPUT_METADATA_INITIALIZED) is not None:
        return

    reference = repository.get(ConfigDataAppKeys.OUTPUT_ARCHIVING_REFERENCE_DATE)
    if reference is None or reference.value is None:
        raise RuntimeError("Output archiving reference date is missing; database migrations must be applied")
    reference_date = datetime.datetime.fromisoformat(reference.value)

    logger.info("Initializing outputs metadata with reference date %s", reference_date)
    studies = study_service.repository.get_all(
        StudyFilter(managed=True, archived=False, access_permissions=AccessPermissions(is_admin=True))
    )
    for study in studies:
        logger.info("Initializing outputs metadata for study %s", study.id)
        output_service.initialize_outputs_metadata(study.id, reference_date)

    repository.save(
        ConfigData(owner=DEFAULT_ADMIN_USER.id, key=ConfigDataAppKeys.OUTPUT_METADATA_INITIALIZED, value="true")
    )


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
) -> tuple[int, list[str]]:
    repository = OutputRepository()
    archived_count = 0
    errors: list[str] = []
    studies = study_service.repository.get_all(
        StudyFilter(managed=True, archived=False, access_permissions=AccessPermissions(is_admin=True))
    )
    for study in studies:
        for output in repository.get_outputs_to_archive(study.id, cutoff):
            try:
                logger.info("Archiving output %s/%s%s", study.id, output.output_id, " [dry-run]" if dry_run else "")
                if dry_run:
                    archived_count += 1
                    continue
                task_id = output_service.archive_output(study.id, output.output_id, last_access_before=cutoff)
                if task_id:
                    _await_archive_task(study_service.task_service, task_id)
                    stored = repository.get(study.id, output.output_id)
                    if stored is not None and stored.archived:
                        archived_count += 1
            except (TaskAlreadyRunning, OutputAlreadyArchived):
                continue
            except Exception as e:
                logger.error("Failed to archive output %s/%s", study.id, output.output_id, exc_info=True)
                errors.append(f"{study.id}/{output.output_id}: {e}")
    return archived_count, errors


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
        if output_service.has_outputs_to_preserve(study_id, output_cutoff):
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
                if not dry_run:
                    _initialize_outputs_metadata(study_service, output_service)
                archived_outputs, errors = _archive_old_outputs(study_service, output_service, output_cutoff, dry_run)
                to_archive = _get_studies_to_archive(study_service, threshold_days)
                logger.info(f"Found {len(to_archive)} studies to archive")

                for study_id in to_archive:
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
