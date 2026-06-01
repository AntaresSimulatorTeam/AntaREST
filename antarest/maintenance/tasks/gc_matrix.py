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
Matrix garbage collection task, agnostic from the way it is executed.

This task deletes unused matrices from the matrix store based on retention time.
"""

import logging
import time

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_file_lock
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus, GarbageCollectorTaskResult, LockId
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


def _delete_matrices(matrix_service: MatrixService, matrices: set[str], dry_run: bool) -> int:
    """Delete matrices and return the number of failures."""
    failures = 0
    for matrix_id in matrices:
        if dry_run:
            logger.info(f"[dry-run] Would delete matrix {matrix_id}")
        else:
            try:
                matrix_service.delete(matrix_id)
                logger.debug(f"Deleted matrix {matrix_id}")
            except Exception as e:
                logger.error(f"Failed to delete matrix {matrix_id}: {e}")
                failures += 1
    return failures


def clean_matrices(matrix_service: MatrixService, dry_run: bool, retention_time: int) -> GarbageCollectorTaskResult:
    """
    Run matrix garbage collection.

    Deletes matrices that are not referenced by any study and older than retention_time.
    """
    start_time = time.time()
    deleted_count = 0
    failures = 0

    logger.info(f"Starting matrix GC (dry_run={dry_run}, retention={retention_time}s)")

    try:
        with db():
            with create_file_lock(lock_id=LockId.MATRIX_GC):
                used_matrices = {m.matrix_id for m in matrix_service.get_used_matrices()}
                matrices = matrix_service.get_matrices()
                saved = {m.id: m.created_at for m in matrices}
                unused = set(saved) - used_matrices

                logger.info(f"Found {len(saved)} matrices, {len(used_matrices)} in use, {len(unused)} unused")

                if unused:
                    now = current_time()
                    # Only delete matrices older than retention_time
                    to_delete = {mid for mid in unused if (now - saved[mid]).total_seconds() >= retention_time}
                    logger.info(f"{len(to_delete)} matrices exceed retention time, will be deleted")

                    failures = _delete_matrices(matrix_service, to_delete, dry_run)
                    deleted_count = len(to_delete) - failures

    except LockNotAcquired:
        logger.warning("Could not acquire lock, another GC is probably running")
        return GarbageCollectorTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
            reason="lock_not_acquired",
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Matrix GC failed", exc_info=e)
        return GarbageCollectorTaskResult(
            status=BackGroundTaskStatus.ERROR,
            error=str(e),
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )

    duration = time.time() - start_time
    status = BackGroundTaskStatus.PARTIAL_SUCCESS if failures else BackGroundTaskStatus.SUCCESS
    logger.info(f"Matrix GC done in {duration:.1f}s: {deleted_count} deleted, {failures} failed")

    return GarbageCollectorTaskResult(
        status=status,
        deleted_count=deleted_count,
        failed_count=failures,
        duration_seconds=duration,
        dry_run=dry_run,
    )
