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

"""Celery task for disk usage logging."""

from celery import Celery

from antarest.core.config import StorageConfig
from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app, logger
from antarest.maintenance.tasks.common import CronParseError, parse_cron_string
from antarest.maintenance.tasks.disk_usage_log import DiskUsageTaskResult, disk_usage_logging


@celery_app.task(
    base=MaintenanceTask,
    bind=True,
    name=TaskName.DISK_USAGE,
    pydantic=True,
)
def disk_usage_log_task(self: MaintenanceTask) -> DiskUsageTaskResult:
    ctx = self.context

    logger.info("Registering disk usage metrics")

    return disk_usage_logging(ctx.config)


def setup_disk_usage_log_task(sender: Celery, storage: "StorageConfig") -> None:
    """

    Setup disk usage logging task with either cron schedule or sleeping time.

    Uses cron if configured, otherwise falls back to sleeping_time.

    Args:
        sender: Celery app instance
        storage: StorageConfig instance

    """
    if storage.disk_usage_log_cron:
        try:
            schedule = parse_cron_string(storage.disk_usage_log_cron)
            sender.add_periodic_task(schedule, disk_usage_log_task.s(), name=TaskName.DISK_USAGE)
            logger.info(f"Disk usage logging registered with cron: {storage.disk_usage_log_cron}")
        except CronParseError as e:
            logger.error(e)
            sender.add_periodic_task(
                storage.disk_usage_log_sleeping_time, disk_usage_log_task.s(), name=TaskName.DISK_USAGE
            )
            logger.info(
                f"Disk usage logging registered with sleeping_time (fallback): "
                f"{storage.disk_usage_log_sleeping_time}s"
            )
    else:
        sender.add_periodic_task(
            storage.disk_usage_log_sleeping_time, disk_usage_log_task.s(), name=TaskName.DISK_USAGE
        )
        logger.info(f"Disk usage logging registered with sleeping_time: {storage.disk_usage_log_sleeping_time}s")
