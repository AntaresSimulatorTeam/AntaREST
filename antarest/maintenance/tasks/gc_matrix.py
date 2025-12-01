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
Matrix garbage collection task for Celery.

This task deletes unused matrices from the matrix store based on retention time.
"""

import logging
import time
from typing import Any, Dict, Set

from sqlalchemy import text

from antarest.celery.app import celery_app
from antarest.celery.context import MaintenanceContext
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)

# PostgreSQL advisory lock ID for matrix GC (prevents concurrent runs)
MATRIX_GC_LOCK_ID = 1001


def _delete_unused_saved_matrices(matrix_service: MatrixService, unused_matrices: Set[str], dry_run: bool) -> None:
    """Delete all files with the name in unused_matrices"""
    logger.info("Deleting unused saved matrices:")
    for unused_matrix_id in unused_matrices:
        logger.info(f"Matrix {unused_matrix_id} is set to be deleted")
        if not dry_run:
            logger.info(f"Deleting {unused_matrix_id}")
            matrix_service.delete(unused_matrix_id)


@celery_app.task(name="antarest.maintenance.tasks.clean_matrices_task")
def clean_matrices_task() -> Dict[str, Any]:
    """
    Delete all matrices that are not used anymore.

    This task:
    1. Acquires a PostgreSQL advisory lock to prevent concurrent execution
    2. Fetches all used matrices and all existing matrices
    3. Compares their lifetimes to the retention_time configuration
    4. Deletes matrices that are unused and exceed the retention period

    Returns:
        dict with execution stats (deleted count, duration, status)
    """
    ctx = MaintenanceContext.get_instance()
    matrix_service = ctx.matrix_service
    config = ctx.config
    assert config is not None, "Config must be initialized"

    # Get configuration
    dry_run = config.storage.matrix_gc_dry_run
    retention_time = config.storage.matrix_gc_retention_time

    start_time = time.time()
    deleted_count = 0

    logger.info("Beginning matrix GC process")
    logger.info(f"Configuration: dry_run={dry_run}, retention_time={retention_time}s")

    try:
        with db():
            logger.info(f"Attempting to acquire advisory lock {MATRIX_GC_LOCK_ID}")
            result = db.session.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": MATRIX_GC_LOCK_ID})
            lock_acquired = result.scalar()

            if not lock_acquired:
                logger.warning(
                    f"Could not acquire advisory lock {MATRIX_GC_LOCK_ID}. "
                    "Another matrix GC process is probably running. Skipping this run."
                )
                return {
                    "status": "skipped",
                    "reason": "lock_not_acquired",
                    "deleted_count": 0,
                    "duration_seconds": time.time() - start_time,
                }

            logger.info(f"Advisory lock {MATRIX_GC_LOCK_ID} acquired successfully")

            # Perform garbage collection
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

            # Lock is automatically released when session ends (commit or rollback)
            logger.info(f"Releasing advisory lock {MATRIX_GC_LOCK_ID}")

    except Exception as e:
        logger.error("Error during matrix GC", exc_info=e)
        return {
            "status": "error",
            "error": str(e),
            "deleted_count": 0,
            "duration_seconds": time.time() - start_time,
        }

    duration = time.time() - start_time
    logger.info(f"Finished matrix GC in {duration}s (deleted {deleted_count} matrices)")

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "duration_seconds": duration,
        "dry_run": dry_run,
    }
