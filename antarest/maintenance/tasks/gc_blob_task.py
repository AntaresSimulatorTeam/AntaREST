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

"""Celery task for blob garbage collection."""

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.common import GCTaskResult
from antarest.maintenance.tasks.gc_blob import clean_blobs


@celery_app.task(bind=True, name="antarest.maintenance.tasks.clean_blobs_task", pydantic=True)
def clean_blobs_task(self: Task) -> GCTaskResult:  # type: ignore[type-arg]
    """Celery wrapper that delegates to clean_blobs()."""
    ctx: MaintenanceContext | None = getattr(self.app.conf, "maintenance_ctx", None)
    if not ctx:
        raise RuntimeError("MaintenanceContext not in app.conf - worker not initialized?")

    return clean_blobs(ctx.blob_service, ctx.config.storage.blob_gc_dry_run)
