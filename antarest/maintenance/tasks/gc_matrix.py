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
from enum import StrEnum
from typing import TYPE_CHECKING, Optional, Set

from pydantic import BaseModel

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.core.utils.utils import current_time
from antarest.matrixstore.service import MatrixService

if TYPE_CHECKING:
    from antarest.maintenance.context import MaintenanceContext


class TaskStatus(StrEnum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


class GCTaskResult(BaseModel):
    """Result of a garbage collection task execution."""

    status: TaskStatus
    deleted_count: int
    duration_seconds: float
    dry_run: Optional[bool] = None
    reason: Optional[str] = None
    error: Optional[str] = None


logger = logging.getLogger(__name__)

MATRIX_GC_LOCK_ID = 1001


def _delete_unused_saved_matrices(matrix_service: MatrixService, unused_matrices: Set[str], dry_run: bool) -> None:
    """Delete all files with the name in unused_matrices"""
    logger.info("Deleting unused saved matrices:")
    for unused_matrix_id in unused_matrices:
        logger.info(f"Matrix {unused_matrix_id} is set to be deleted")
        if not dry_run:
            logger.info(f"Deleting {unused_matrix_id}")
            matrix_service.delete(unused_matrix_id)


def clean_matrices(
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
            with create_lock(db.session, lock_id=MATRIX_GC_LOCK_ID):
                used_matrices = {matrix.matrix_id for matrix in matrix_service.get_used_matrices()}
                all_existing_matrices = matrix_service.get_matrices()
                saved_matrices = {matrix.id: matrix.created_at for matrix in all_existing_matrices}
                unused_matrices = set(saved_matrices) - used_matrices

                logger.info(
                    f"Matrix statistics: "
                    f"total={len(saved_matrices)}, "
                    f"used={len(used_matrices)}, "
                    f"unused={len(unused_matrices)}"
                )

                if unused_matrices:
                    # Compare for each matrix, its lifetime duration to the `retention_time` value.
                    # If it's more, remove the matrix. Otherwise, pass.
                    matrices_to_remove = set()
                    now = current_time()
                    for matrix in unused_matrices:
                        matrix_lifetime = (now - saved_matrices[matrix]).total_seconds()
                        if matrix_lifetime >= retention_time:
                            matrices_to_remove.add(matrix)

                    deleted_count = len(matrices_to_remove)
                    logger.info(f"Matrices to remove: {deleted_count}")

                    _delete_unused_saved_matrices(
                        matrix_service=matrix_service, unused_matrices=matrices_to_remove, dry_run=dry_run
                    )

    except LockNotAcquired:
        logger.warning(
            f"Could not acquire advisory lock {MATRIX_GC_LOCK_ID}. "
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
    logger.info(f"Finished matrix GC in {duration}s (deleted {deleted_count} matrices)")

    return GCTaskResult(
        status=TaskStatus.SUCCESS,
        deleted_count=deleted_count,
        duration_seconds=duration,
        dry_run=dry_run,
    )


def clean_matrices_task(ctx: "Optional[MaintenanceContext]" = None) -> GCTaskResult:
    """
    Celery task wrapper for matrix garbage collection.

    This function extracts the required arguments from the MaintenanceContext
    and delegates to the clean_matrices function.

    Args:
        ctx: Optional context for dependency injection (used in tests).
             If None, uses the singleton instance.

    Returns:
        GCTaskResult with execution stats

    Raises:
        RuntimeError: If MaintenanceContext config is not initialized
    """
    # Import here to avoid circular import
    from antarest.maintenance.context import MaintenanceContext

    if ctx is None:
        ctx = MaintenanceContext.get_instance()
    if ctx.config is None:
        raise RuntimeError("MaintenanceContext config is not initialized")

    return clean_matrices(
        matrix_service=ctx.matrix_service,
        dry_run=ctx.config.storage.matrix_gc_dry_run,
        retention_time=ctx.config.storage.matrix_gc_retention_time,
    )
