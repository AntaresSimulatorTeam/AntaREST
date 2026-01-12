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

"""Celery task for watcher scan."""

from celery import Task

from antarest.maintenance.app import celery_app
from antarest.maintenance.context import MaintenanceContext
from antarest.maintenance.tasks.common import WatcherScanTaskResult
from antarest.maintenance.tasks.watcher_scan import scan_workspaces


@celery_app.task(bind=True, name="watcher_scan", pydantic=True)
def watcher_scan_task(self: Task) -> WatcherScanTaskResult:  # type: ignore[type-arg]
    """Celery wrapper that delegates to scan_workspaces()."""
    ctx: MaintenanceContext | None = self.app.conf.get("maintenance_ctx")
    if not ctx:
        raise RuntimeError("MaintenanceContext not in app.conf - worker not initialized?")

    return scan_workspaces(
        ctx.config,
        ctx.study_service,
        ctx.config.storage.watcher_scan_dry_run,
    )
