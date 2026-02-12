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
from antarest.core.tasks.model import TaskListFilter
from antarest.core.tasks.service import TaskJobService


def gc_tasks(task_job_service: TaskJobService, task_retention_duration_date: int):
    task_filter = TaskListFilter(from_creation_date_utc=task_retention_duration_date)
    gc_task_list = task_job_service.list_tasks(task_filter)
    pass