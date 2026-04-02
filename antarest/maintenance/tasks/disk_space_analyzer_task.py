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

"""Task to analyze disk space usage."""

import logging
from typing import TYPE_CHECKING

from celery import Celery

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import CronParseError, parse_cron_string
from antarest.maintenance.tasks.disk_space_analyzer import DiskSpaceAnalyzerTaskResult, disk_space_analysis

if TYPE_CHECKING:
    from antarest.core.config import StorageConfig

logger = logging.getLogger(__name__)


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.DISK_SPACE_ANALYZER, pydantic=True)
def disk_space_analyzer_task(self: MaintenanceTask) -> DiskSpaceAnalyzerTaskResult:
    """Celery task to analyze disk space usage by study."""
    ctx = self.context

    with current_user_context(DEFAULT_ADMIN_USER):
        return disk_space_analysis(ctx.study_service, ctx.study_disk_space_repository)


def setup_disk_space_analyzer_task(sender: Celery, storage: "StorageConfig") -> None:
    """
    Setup disk space analyzer task with either cron schedule or sleeping time.

    Uses cron if configured, otherwise falls back to sleeping_time.

    Args:
        sender: Celery app instance
        storage: StorageConfig instance
    """
    if storage.disk_space_analyzer_cron:
        try:
            schedule = parse_cron_string(storage.disk_space_analyzer_cron)
            sender.add_periodic_task(schedule, disk_space_analyzer_task.s(), name=TaskName.DISK_SPACE_ANALYZER)
            logger.info(f"Disk usage logging registered with cron: {storage.disk_usage_log_cron}")
        except CronParseError as e:
            logger.error(e)
            sender.add_periodic_task(
                storage.disk_space_analyzer_sleeping_time,
                disk_space_analyzer_task.s(),
                name=TaskName.DISK_SPACE_ANALYZER,
            )
            logger.info(
                f"Disk space analyzer registered with sleeping_time: {storage.disk_space_analyzer_sleeping_time}s"
            )
    else:
        sender.add_periodic_task(
            storage.disk_space_analyzer_sleeping_time, disk_space_analyzer_task.s(), name=TaskName.DISK_SPACE_ANALYZER
        )
        logger.info(f"Disk space analyzer registered with sleeping_time: {storage.disk_space_analyzer_sleeping_time}s")
