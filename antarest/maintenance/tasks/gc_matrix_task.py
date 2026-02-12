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

from celery import Task

from antarest.maintenance.app import TaskName, celery_app, get_maintenance_context
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult
from antarest.maintenance.tasks.gc_matrix import clean_matrices


@celery_app.task(bind=True, name=TaskName.MATRICES_CLEANER, pydantic=True)
def clean_matrices_task(self: Task) -> GarbageCollectorTaskResult:  # type: ignore[type-arg]
    """Celery wrapper that delegates to clean_matrices()."""
    ctx = get_maintenance_context(self)
    return clean_matrices(
        ctx.matrix_service,
        ctx.config.storage.matrix_gc_dry_run,
        ctx.config.storage.matrix_gc_retention_time,
    )
