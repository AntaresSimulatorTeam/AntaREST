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

"""Celery task for blob garbage collection."""

import logging

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult, MaintenanceContextNotFoundError, TRANSIENT_ERRORS
from antarest.maintenance.tasks.gc_blob import clean_blobs

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="blobs_cleaner",
    autoretry_for=TRANSIENT_ERRORS,
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=3600,
    retry_jitter=True,
)
def clean_blobs_task(self: Task) -> GarbageCollectorTaskResult:  # type: ignore[type-arg]
    """
    Celery wrapper that delegates to clean_blobs().

    This task runs once a day and cleans unused blobs.
    If it fails, it will retry up to 3 times with exponential backoff:
    - Retry 1: ~5 minutes
    - Retry 2: ~10 minutes
    - Retry 3: ~20 minutes
    Total retry window: ~35 minutes
    """
    if self.request.retries > 0:
        logger.warning(f"Blob GC retry attempt {self.request.retries}/3")

    ctx: MaintenanceContext | None = self.app.conf.get("maintenance_ctx")
    if not ctx:
        logger.error("MaintenanceContext not found - worker not initialized?")
        raise MaintenanceContextNotFoundError()

    return clean_blobs(ctx.blob_service, ctx.config.storage.blob_gc_dry_run)
