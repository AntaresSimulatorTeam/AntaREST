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
from datetime import datetime, timezone

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from antarest.core.tasks.model import TaskJob, TaskStatus
from antarest.tools.admin_lib import fix_interrupted_tasks_status


@pytest.mark.parametrize(
    ("status", "result_status", "result_msg"),
    [
        (TaskStatus.RUNNING.value, False, "task ongoing"),
        (TaskStatus.PENDING.value, True, "task pending"),
        (TaskStatus.FAILED.value, False, "task failed"),
        (TaskStatus.COMPLETED.value, True, "task finished"),
        (TaskStatus.TIMEOUT.value, False, "task timed out"),
        (TaskStatus.CANCELLED.value, True, "task canceled"),
    ],
)
def test_fix_tasks_status(
    db_engine: Engine,
    status: int,
    result_status: bool,
    result_msg: str,
) -> None:
    max_diff_seconds: int = 1
    test_id: str = "2ea94758-9ea5-4015-a45f-b245a6ffc147"

    completion_date: datetime = datetime.now(timezone.utc).replace(tzinfo=None)
    task_job = TaskJob(
        id=test_id,
        name="test",
        status=status,
        result_status=result_status,
        result_msg=result_msg,
        completion_date=completion_date,
    )
    make_session = sessionmaker(bind=db_engine)
    with make_session() as session:
        session.add(task_job)
        session.commit()
    fix_interrupted_tasks_status(db_engine)
    with make_session() as session:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if status in [TaskStatus.RUNNING.value, TaskStatus.PENDING.value]:
            update_tasks_count = (
                session.query(TaskJob)
                .filter(TaskJob.status.in_([TaskStatus.RUNNING.value, TaskStatus.PENDING.value]))
                .count()
            )
            assert not update_tasks_count
            updated_task_job = session.query(TaskJob).get(test_id)
            assert updated_task_job.status == TaskStatus.FAILED.value
            assert not updated_task_job.result_status
            assert updated_task_job.result_msg == "Task was interrupted due to server restart"
            assert (now - updated_task_job.completion_date).seconds <= max_diff_seconds
        else:
            updated_task_job = session.query(TaskJob).get(test_id)
            assert updated_task_job.status == status
            assert updated_task_job.result_status == result_status
            assert updated_task_job.result_msg == result_msg
            assert (now - updated_task_job.completion_date).seconds <= max_diff_seconds
