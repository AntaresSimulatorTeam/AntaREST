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

"""Celery task for auto-archiving old studies."""

import logging
from typing import TYPE_CHECKING

from celery import Celery, Task

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import (
    TRANSIENT_ERRORS,
    CronParseError,
    MaintenanceContextNotFoundError,
    parse_cron_string,
)

if TYPE_CHECKING:
    from antarest.core.config import StorageConfig

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="auto_archiver",
    autoretry_for=TRANSIENT_ERRORS,
    retry_kwargs={"max_retries": 5},
    retry_backoff=True,
    retry_backoff_max=7200,
    retry_jitter=True,
)
def auto_archive_task(self: Task) -> AutoArchiveTaskResult:  # type: ignore[type-arg]
    """
    Celery wrapper that delegates to archive_old_studies() with admin context.

    This task runs every day at night and archives old studies.
    If it fails, it will retry up to 5 times with exponential backoff:
    - Retry 1: ~5 minutes
    - Retry 2: ~10 minutes
    - Retry 3: ~20 minutes
    - Retry 4: ~40 minutes
    - Retry 5: ~80 minutes
    Total retry window: ~2.5 hours
    """
    if self.request.retries > 0:
        logger.warning(f"Auto-archive retry attempt {self.request.retries}/5")

    ctx: MaintenanceContext | None = self.app.conf.get("maintenance_ctx")
    if not ctx:
        raise MaintenanceContextNotFoundError()

    with current_user_context(DEFAULT_ADMIN_USER):
        return archive_old_studies(
            ctx.study_service,
            ctx.output_service,
            ctx.config.storage.auto_archive_threshold_days,
            ctx.config.storage.snapshot_retention_days,
            ctx.config.storage.auto_archive_dry_run,
        )


def setup_auto_archive_task(sender: Celery, storage: "StorageConfig") -> None:
    """
    Setup auto-archive task with either cron schedule or sleeping time.

    Uses cron if configured, otherwise falls back to sleeping_time.

    Args:
        sender: Celery app instance
        storage: StorageConfig instance
    """
    if storage.auto_archive_cron:
        try:
            schedule = parse_cron_string(storage.auto_archive_cron)
            sender.add_periodic_task(schedule, auto_archive_task.s(), name="auto_archiver")
        except CronParseError as e:
            logger.error(e)
            sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")
            logger.info(f"Auto-archive registered with sleeping_time: {storage.auto_archive_sleeping_time}s")
    else:
        sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")
        logger.info(f"Auto-archive registered with sleeping_time: {storage.auto_archive_sleeping_time}s")
