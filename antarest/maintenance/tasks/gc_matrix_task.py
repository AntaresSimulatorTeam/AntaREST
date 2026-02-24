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

"""Celery task for matrix garbage collection."""

from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult
from antarest.maintenance.tasks.gc_matrix import clean_matrices


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.MATRICES_CLEANER, pydantic=True)
def clean_matrices_task(self: MaintenanceTask) -> GarbageCollectorTaskResult:
    """Celery wrapper that delegates to clean_matrices()."""
    ctx = self.context
    return clean_matrices(
        ctx.matrix_service,
        ctx.config.storage.matrix_gc_dry_run,
        ctx.config.storage.matrix_gc_retention_time,
    )
