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

from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app, logger
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

    return disk_usage_logging(ctx.config, ctx.config.storage.disk_usage_dry_run)
