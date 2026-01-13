# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
Matrix garbage collection task, agnostic from the way it is executed.

This task deletes unused matrices from the matrix store based on retention time.
"""

import logging
import time
from collections.abc import Sequence
from datetime import timedelta
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import or_

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.core.utils.utils import current_time
from antarest.matrixstore.service import MatrixService
from antarest.study.output.output_model import OutputVariablesViewsModel


class TaskStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SKIPPED = "skipped"
    ERROR = "error"


class GCTaskResult(BaseModel):
    """Result of a garbage collection task execution."""

    status: TaskStatus
    deleted_count: int
    failed_count: int = 0
    duration_seconds: float
    dry_run: Optional[bool] = None
    reason: Optional[str] = None
    error: Optional[str] = None


logger = logging.getLogger(__name__)

VV_GC_LOCK_ID = 1001


def _delete_matrices(matrix_service: MatrixService, matrix_ids: Sequence[str], dry_run: bool) -> int:
    failures = 0
    for mid in matrix_ids:
        if not dry_run:
            try:
                matrix_service.delete(mid)
            except Exception as e:
                logger.error("Failed to delete matrix %s: %s", mid, e)
                failures += 1
    return failures


def clean_variable_views(
    matrix_service: MatrixService,
    dry_run: bool,
    retention_time: int,
) -> GCTaskResult:
    """
    Core logic for matrix garbage collection.

    This function:
    1. Acquires a PostgreSQL advisory lock to prevent concurrent execution
    2. Fetches all used matrices and all existing matrices
    3. Compares their lifetimes to the retention_time configuration
    4. Deletes matrices that are unused and exceed the retention period

    Args:
        matrix_service: Service for matrix operations
        dry_run: If True, don't actually delete matrices
        retention_time: Time in seconds before unused matrices can be deleted

    Returns:
        GCTaskResult with execution stats (deleted count, duration, status)
    """
    start_time = time.time()
    deleted_count = 0

    logger.info("Beginning matrix GC process")
    logger.info(f"Configuration: dry_run={dry_run}, retention_time={retention_time}s")

    try:
        with db():
            with create_lock(db.session, lock_id=VV_GC_LOCK_ID):
                failures = 0
                deleted = 0
                cutoff = current_time() - timedelta(days=retention_time)

                rows = (
                    db.session.query(OutputVariablesViewsModel)
                    .filter(or_(OutputVariablesViewsModel.last_read < cutoff))
                    .all()
                )
                if not rows:
                    return GCTaskResult(
                        status=TaskStatus.SKIPPED,
                        reason="no_unused_variale_view",
                        deleted_count=0,
                        duration_seconds=time.time() - start_time,
                    )

                matrix_ids = [r.matrix_id for r in rows]

                logger.info("VBV GC: deleting %d view rows (dry_run=%s)", len(rows), dry_run)

                if not dry_run:
                    for r in rows:
                        db.session.delete(r)
                    db.session.commit()

                deleted += len(rows)

                # Delete matrices after deleting view rows so they become "unused"
                failures += _delete_matrices(matrix_service, matrix_ids, dry_run=dry_run)

    except LockNotAcquired:
        logger.warning(
            f"Could not acquire advisory lock {VV_GC_LOCK_ID}. "
            "Another matrix GC process is probably running. Skipping this run."
        )
        return GCTaskResult(
            status=TaskStatus.SKIPPED,
            reason="lock_not_acquired",
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Error during matrix GC", exc_info=e)
        return GCTaskResult(
            status=TaskStatus.ERROR,
            error=str(e),
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )

    duration = time.time() - start_time
    status = TaskStatus.PARTIAL_SUCCESS if failures > 0 else TaskStatus.SUCCESS
    logger.info(f"Finished matrix GC in {duration}s (deleted {deleted_count}, failed {failures})")

    return GCTaskResult(
        status=status,
        deleted_count=deleted_count,
        failed_count=failures,
        duration_seconds=duration,
        dry_run=dry_run,
    )
