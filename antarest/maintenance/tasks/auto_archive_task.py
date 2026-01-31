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
from celery.schedules import crontab

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import TRANSIENT_ERRORS, MaintenanceContextNotFoundError

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

    This task runs once a week (by default: Saturday at midnight) and archives old studies.
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


def setup_auto_archive_task(sender: Celery, storage: "StorageConfig", desktop_mode: bool) -> None:
    """
    Setup auto-archive task with either cron schedule or sleeping time.

    In desktop mode, always uses sleeping_time regardless of cron configuration.
    In web mode, uses cron if configured, otherwise falls back to sleeping_time.

    Args:
        sender: Celery app instance
        storage: StorageConfig instance
        desktop_mode: Whether running in desktop mode
    """
    # Desktop mode: always use sleeping_time
    if desktop_mode:
        sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")
        logger.info(f"Auto-archive registered (desktop mode) with sleeping_time: {storage.auto_archive_sleeping_time}s")
        return

    # Web mode: use cron if configured (non-empty string), otherwise sleeping_time
    if storage.auto_archive_cron and storage.auto_archive_cron.strip():
        # Parse cron string (format: "minute hour day_of_month month day_of_week")
        cron_parts = storage.auto_archive_cron.split()
        if len(cron_parts) == 5:
            schedule = crontab(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day_of_month=cron_parts[2],
                month_of_year=cron_parts[3],
                day_of_week=cron_parts[4],
            )
            sender.add_periodic_task(schedule, auto_archive_task.s(), name="auto_archiver")
            logger.info(f"Auto-archive registered (web mode) with cron schedule: {storage.auto_archive_cron}")
        else:
            logger.error(
                f"Invalid cron format: '{storage.auto_archive_cron}'. "
                f"Expected 5 fields (minute hour day_of_month month day_of_week), got {len(cron_parts)}. "
                f"Falling back to sleeping_time={storage.auto_archive_sleeping_time}s"
            )
            sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")
    else:
        sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")
        logger.info(f"Auto-archive registered (web mode) with sleeping_time: {storage.auto_archive_sleeping_time}s")
