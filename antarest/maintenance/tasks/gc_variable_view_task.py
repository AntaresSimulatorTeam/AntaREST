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

"""
Output variables views garbage collection task wrapper for Celery.

This task deletes old materialized output variables views based on their last_read timestamp.
"""

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.gc_variable_view import GCTaskResult, clean_variable_views


@celery_app.task(bind=True, name="antarest.maintenance.tasks.clean_variable_views_task", pydantic=True)
def clean_variable_views_task(self: Task) -> GCTaskResult:  # type: ignore[type-arg]
    """
    Celery task wrapper for clean_variable_views.

    Retrieves dependencies from the Celery app configuration (injected during worker init)
    and delegates to clean_variable_views().

    Args:
        self: The bound task instance, provides access to self.app
    """
    ctx: MaintenanceContext | None = getattr(self.app.conf, "maintenance_ctx", None)
    if ctx is None:
        raise RuntimeError("MaintenanceContext not found in app.conf. Ensure worker was properly started.")

    return clean_variable_views(
        matrix_service=ctx.matrix_service,
        dry_run=ctx.config.storage.variable_view_gc_dry_run,
        retention_time=ctx.config.storage.variable_view_gc_retention_time,
    )
