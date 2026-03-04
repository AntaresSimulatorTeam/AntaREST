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

"""Integration tests for the tasks cleaning garbage collection task."""

from datetime import datetime
from unittest.mock import patch

from helpers import with_admin_user

from antarest.core.tasks.model import TaskDTO, TaskJob, TaskListFilter, TaskStatus
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.maintenance.tasks.gc_tasks import clean_tasks


class TestTasksGCIntegration:
    @with_admin_user
    def test_clean_tasks_gc(self, task_service: ITaskService, task_job_repository: TaskJobRepository):
        task_1 = TaskJob(
            id="1", status=TaskStatus.RUNNING.value, name="task_1", creation_date=datetime(2026, 1, 1, 10, 0, 0)
        )
        task_2 = TaskJob(
            id="2", status=TaskStatus.RUNNING.value, name="task_2", creation_date=datetime(2026, 1, 15, 14, 30, 0)
        )
        task_3 = TaskJob(
            id="3", status=TaskStatus.RUNNING.value, name="task_3", creation_date=datetime(2026, 2, 1, 8, 45, 0)
        )
        task_4 = TaskJob(
            id="4", status=TaskStatus.RUNNING.value, name="task_4", creation_date=datetime(2026, 2, 18, 23, 59, 59)
        )

        with db():
            task_job_repository.save(task_1)
            task_job_repository.save(task_2)
            task_job_repository.save(task_3)
            task_job_repository.save(task_4)

            task_list = task_service.list_tasks(TaskListFilter())
            assert len(task_list) == 4

            # deleting tasks
            with patch("antarest.core.utils.utils.current_time", return_value=datetime(2026, 2, 20, 0, 0, 0)):
                task_result = clean_tasks(task_service=task_service, dry_run=False, task_retention_duration=17)

            expected_task = TaskDTO(
                id="4",
                status=TaskStatus.RUNNING,
                name="task_4",
                creation_date_utc=str(datetime(2026, 2, 18, 23, 59, 59)),
            )
            assert task_result.deleted_count == 3

            task_list = task_service.list_tasks(TaskListFilter())
            assert len(task_list) == 1
            assert task_list == [expected_task]

    def test_returns_skipped_when_lock_held(self, task_service: ITaskService):
        with db():
            with create_lock(db.session, lock_id=LockId.TASKS_GC):
                result = clean_tasks(task_service=task_service, dry_run=False, task_retention_duration=60)

            assert result.status == BackGroundTaskStatus.SKIPPED
            assert result.reason == "lock_not_acquired"
