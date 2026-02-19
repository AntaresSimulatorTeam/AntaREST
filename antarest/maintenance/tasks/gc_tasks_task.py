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

"""Celery task for regular purge of task table."""

from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import GarbageCollectorTaskResult
from antarest.maintenance.tasks.gc_tasks import clean_tasks


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.TASKS_CLEANER, pydantic=True)
def gc_tasks_task(self: MaintenanceTask) -> GarbageCollectorTaskResult:
    ctx = self.context

    return clean_tasks(
        ctx.task_service, ctx.config.storage.tasks_gc_dry_run, ctx.config.storage.tasks_gc_retention_duration
    )
