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
Matrix garbage collection task wrapper for Celery.

This task deletes unused matrices from the matrix store based on retention time.
"""

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.gc_matrix import GCTaskResult, clean_matrices


@celery_app.task(bind=True, name="antarest.maintenance.tasks.clean_matrices_task", pydantic=True)
def clean_matrices_task(self: Task) -> GCTaskResult:  # type: ignore[type-arg]
    """
    Celery task wrapper for clean_matrices.

    Retrieves dependencies from the Celery app configuration (injected during worker init)
    and delegates to clean_matrices().

    Args:
        self: The bound task instance, provides access to self.app
    """
    ctx: MaintenanceContext | None = getattr(self.app.conf, "maintenance_ctx", None)
    if ctx is None:
        raise RuntimeError("MaintenanceContext not found in app.conf. Ensure worker was properly started.")

    return clean_matrices(
        matrix_service=ctx.matrix_service,
        dry_run=ctx.config.storage.matrix_gc_dry_run,
        retention_time=ctx.config.storage.matrix_gc_retention_time,
    )
