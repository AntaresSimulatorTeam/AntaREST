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

"""
Variable view garbage collection task, agnostic from the way it is executed.
This task deletes unused variable views from the variable view store based on retention time.
"""

import logging
import time
from datetime import timedelta

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus, GarbageCollectorTaskResult, LockId
from antarest.output.variable_view.db import OutputVariablesViewsModel

logger = logging.getLogger(__name__)


def clean_variable_views(
    dry_run: bool,
    retention_time: int,
) -> GarbageCollectorTaskResult:
    """
    Delete variable views if their last_read is older than retention_time.

    Note: matrices are not deleted here. Once a row is deleted from OutputVariablesViewsModel,
    its matrix id is not returned anymore by the variable view usage provider, so the matrix
    for that view becomes eligible for matrix GC.

    Args:
        dry_run: If True, don't actually delete variable views rows
        retention_time: Time in days before unused variable views can be deleted
    Returns:
        GarbageCollectorTaskResult with execution stats (deleted count, duration, status)
    """
    start_time = time.time()

    logger.info("Beginning variables view GC process")
    logger.info(f"Configuration: dry_run={dry_run}, retention_time={retention_time} days")

    deleted_count = 0
    try:
        with db():
            with create_lock(db.session, lock_id=LockId.VARIABLE_VIEW_GC):
                cutoff = current_time() - timedelta(days=retention_time)

                query = db.session.query(OutputVariablesViewsModel).filter(OutputVariablesViewsModel.last_read < cutoff)

                if dry_run:
                    deleted_count = query.count()
                else:
                    deleted_count = query.delete()
                    db.session.commit()

                if deleted_count == 0:
                    return GarbageCollectorTaskResult(
                        status=BackGroundTaskStatus.SKIPPED,
                        reason="no_unused_variable_view",
                        deleted_count=0,
                        duration_seconds=time.time() - start_time,
                    )

                logger.info("Variable view GC: deleted %d view rows (dry_run=%s)", deleted_count, dry_run)

    except LockNotAcquired:
        logger.warning(
            f"Could not acquire advisory lock {LockId.VARIABLE_VIEW_GC}. "
            "Another variable GC process is probably running. Skipping this run."
        )
        return GarbageCollectorTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            reason="lock_not_acquired",
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Error during variable view GC", exc_info=e)
        return GarbageCollectorTaskResult(
            status=BackGroundTaskStatus.ERROR,
            error=str(e),
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )

    duration = time.time() - start_time
    logger.info(f"Finished variable view GC in {duration}s (deleted {deleted_count})")

    return GarbageCollectorTaskResult(
        status=BackGroundTaskStatus.SUCCESS,
        deleted_count=deleted_count,
        duration_seconds=duration,
        dry_run=dry_run,
    )
