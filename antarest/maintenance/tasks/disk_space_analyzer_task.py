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

"""Task to analyze disk space usage."""

from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.disk_space_analyzer import DiskSpaceAnalyzerTaskResult, disk_space_analysis


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.DISK_SPACE_ANALYZER, pydantic=True)
def disk_space_analyzer_task(self: MaintenanceTask) -> DiskSpaceAnalyzerTaskResult:
    """Celery task to analyze disk space usage by study."""
    ctx = self.context

    return disk_space_analysis(ctx.study_service, ctx.study_disk_space_repository)
