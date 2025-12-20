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

"""Blob garbage collection task."""

import logging
import time
from typing import Set

from antarest.blobstore.service import BlobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_lock
from antarest.maintenance.tasks.common import GCTaskResult, LockId, TaskStatus

logger = logging.getLogger(__name__)


def _delete_blobs(blob_service: BlobService, blobs: Set[str], dry_run: bool) -> int:
    """Delete blobs and return the number of failures."""
    failures = 0
    for blob_id in blobs:
        if dry_run:
            logger.info(f"[dry-run] Would delete blob {blob_id}")
        else:
            try:
                blob_service.delete(blob_id)
                logger.debug(f"Deleted blob {blob_id}")
            except Exception as e:
                logger.error(f"Failed to delete blob {blob_id}: {e}")
                failures += 1
    return failures


def clean_blobs(blob_service: BlobService, dry_run: bool) -> GCTaskResult:
    """Run blob garbage collection. Deletes blobs not referenced by any study."""
    start_time = time.time()
    deleted_count = 0
    failures = 0

    logger.info(f"Starting blob GC (dry_run={dry_run})")

    try:
        with db():
            with create_lock(db.session, lock_id=LockId.BLOB_GC):
                used_blobs = {blob.blob_id for blob in blob_service.get_used_blobs()}
                saved_blobs = blob_service.get_saved_blobs()
                unused_blobs = set(saved_blobs) - used_blobs

                logger.info(f"Found {len(saved_blobs)} blobs, {len(used_blobs)} in use, {len(unused_blobs)} to delete")

                if unused_blobs:
                    failures = _delete_blobs(blob_service, unused_blobs, dry_run)
                    deleted_count = len(unused_blobs) - failures

    except LockNotAcquired:
        logger.warning("Could not acquire lock, another GC is probably running")
        return GCTaskResult(
            status=TaskStatus.SKIPPED,
            reason="lock_not_acquired",
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Blob GC failed", exc_info=e)
        return GCTaskResult(
            status=TaskStatus.ERROR,
            error=str(e),
            deleted_count=0,
            duration_seconds=time.time() - start_time,
        )

    duration = time.time() - start_time
    status = TaskStatus.PARTIAL_SUCCESS if failures else TaskStatus.SUCCESS
    logger.info(f"Blob GC done in {duration:.1f}s: {deleted_count} deleted, {failures} failed")

    return GCTaskResult(
        status=status,
        deleted_count=deleted_count,
        failed_count=failures,
        duration_seconds=duration,
        dry_run=dry_run,
    )
