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
Output variables views garbage collection task wrapper for Celery.
This task deletes old materialized output variables views based on their last_read timestamp.
"""

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult, MaintenanceContextNotFoundError
from antarest.maintenance.tasks.gc_variable_view import clean_variable_views


@celery_app.task(bind=True, name="variable_view_cleaner", pydantic=True)
def clean_variable_views_task(self: Task) -> GarbageCollectorTaskResult:  # type: ignore[type-arg]
    """
    Celery task wrapper for clean_variable_views.
    """
    ctx: MaintenanceContext | None = self.app.conf.get("maintenance_ctx")
    if ctx is None:
        raise MaintenanceContextNotFoundError()

    return clean_variable_views(
        dry_run=ctx.config.storage.variable_view_gc_dry_run,
        retention_time=ctx.config.storage.variable_view_gc_retention_days,
    )
