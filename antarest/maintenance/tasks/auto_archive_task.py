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

"""Celery task for auto-archiving old studies."""

from celery import Task

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.auto_archive import AutoArchiveTaskResult, archive_old_studies
from antarest.maintenance.tasks.common import MaintenanceContextNotFoundError


@celery_app.task(bind=True, name="auto_archiver", pydantic=True)
def auto_archive_task(self: Task) -> AutoArchiveTaskResult:  # type: ignore[type-arg]
    """Celery wrapper that delegates to archive_old_studies() with admin context."""
    ctx: MaintenanceContext | None = self.app.conf.get("maintenance_ctx")
    if not ctx:
        raise MaintenanceContextNotFoundError()

    with current_user_context(DEFAULT_ADMIN_USER):
        return archive_old_studies(
            ctx.study_service,
            ctx.output_service,
            ctx.config.storage.auto_archive_threshold_days,
            ctx.config.storage.snapshot_retention_days,
            ctx.config.storage.auto_archive_dry_run,
        )
