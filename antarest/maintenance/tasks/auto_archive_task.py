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

"""Celery task for auto-archiving old studies."""

from celery import Task

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies


@celery_app.task(bind=True, name="antarest.maintenance.tasks.auto_archive_task", pydantic=True)
def auto_archive_task(self: Task) -> AutoArchiveTaskResult:  # type: ignore[type-arg]
    """Celery wrapper that delegates to archive_old_studies() with admin context."""
    ctx: MaintenanceContext | None = getattr(self.app.conf, "maintenance_ctx", None)
    if not ctx:
        raise RuntimeError("MaintenanceContext not in app.conf - worker not initialized?")

    with current_user_context(DEFAULT_ADMIN_USER):
        return archive_old_studies(
            ctx.study_service,
            ctx.output_service,
            ctx.config.storage.auto_archive_threshold_days,
            ctx.config.storage.snapshot_retention_days,
            ctx.config.storage.auto_archive_dry_run,
        )
