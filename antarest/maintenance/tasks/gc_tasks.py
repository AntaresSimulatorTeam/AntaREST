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

from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_file_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, GarbageCollectorTaskResult, LockId

logger = logging.getLogger(__name__)


def clean_tasks(task_service: ITaskService, dry_run: bool, task_retention_duration: int) -> GarbageCollectorTaskResult:
    start_time = time.time()
    deleted_count = 0
    try:
        with db():
            with create_file_lock(lock_id=LockId.TASKS_GC):
                logger.info(f"Deleting tasks older than {task_retention_duration} days from the database")
                if not dry_run:
                    deleted_count = task_service.delete_task_by_creation_date(task_retention_duration)
                else:
                    logger.info(f"[dry-run] Would delete tasks older than {task_retention_duration} days")
                    deleted_count = 0

        duration_seconds = time.time() - start_time

    except LockNotAcquired:
        logger.warning(f"Could not acquire lock {LockId.TASKS_GC}, another GC is probably running")
        return GarbageCollectorTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            reason="lock_not_acquired",
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )

    logger.info(f"Finished tasks GC in {duration_seconds}s (deleted {deleted_count})")

    return GarbageCollectorTaskResult(
        status=BackGroundTaskStatus.SUCCESS,
        deleted_count=deleted_count,
        duration_seconds=duration_seconds,
        dry_run=dry_run,
    )
