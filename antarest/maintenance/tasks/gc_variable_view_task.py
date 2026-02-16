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

from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult
from antarest.maintenance.tasks.gc_variable_view import clean_variable_views


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.VARIABLE_VIEW_CLEANER, pydantic=True)
def clean_variable_views_task(self: MaintenanceTask) -> GarbageCollectorTaskResult:
    """
    Celery task wrapper for clean_variable_views.
    """
    ctx = self.context
    return clean_variable_views(
        dry_run=ctx.config.storage.variable_view_gc_dry_run,
        retention_time=ctx.config.storage.variable_view_gc_retention_days,
    )
