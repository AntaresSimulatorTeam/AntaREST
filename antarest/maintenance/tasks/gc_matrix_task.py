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

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.gc_matrix import GCTaskResult, clean_matrices


@celery_app.task(name="antarest.maintenance.tasks.clean_matrices_task", pydantic=True)
def clean_matrices_task() -> GCTaskResult:
    """
    Celery task wrapper for clean_matrices.

    Retrieves dependencies from the worker context and delegates to clean_matrices().
    """
    ctx = MaintenanceContext.get_instance()
    if ctx.config is None:
        raise RuntimeError("MaintenanceContext config is not initialized. Ensure worker was properly started.")

    return clean_matrices(
        matrix_service=ctx.matrix_service,
        dry_run=ctx.config.storage.matrix_gc_dry_run,
        retention_time=ctx.config.storage.matrix_gc_retention_time,
    )
