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
from datetime import datetime

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from antarest.core.tasks.model import TaskJob, TaskStatus
from antarest.core.utils.utils import current_time
from antarest.tools.admin_lib import _do_fix_interrupted_tasks_status


def test_fix_tasks_status(db_engine: Engine) -> None:
    completed_task = TaskJob(
        id="completed",
        name="completed",
        status=TaskStatus.COMPLETED.value,
        result_status=True,
        result_msg="success",
        completion_date=datetime(2025, 6, 1, 12, 0, 0),
    )
    failed_task = TaskJob(
        id="failed",
        name="failed",
        status=TaskStatus.FAILED.value,
        result_status=False,
        result_msg="failed",
        completion_date=datetime(2025, 6, 1, 12, 0, 0),
    )
    running_task = TaskJob(
        id="running",
        name="running",
        status=TaskStatus.RUNNING.value,
    )
    pending_task = TaskJob(
        id="pending",
        name="pending",
        status=TaskStatus.PENDING.value,
    )
    timeout_task = TaskJob(
        id="timeout",
        name="timeout",
        status=TaskStatus.TIMEOUT.value,
        result_status=False,
        result_msg="timed out",
        completion_date=datetime(2025, 6, 1, 12, 0, 0),
    )
    cancelled_task = TaskJob(
        id="cancelled",
        name="cancelled",
        status=TaskStatus.CANCELLED.value,
        result_status=False,
        result_msg="was cancelled",
        completion_date=datetime(2025, 6, 1, 12, 0, 0),
    )
    make_session = sessionmaker(bind=db_engine)
    with make_session() as session:
        session.add_all([pending_task, running_task, failed_task, completed_task, timeout_task, cancelled_task])
        session.commit()

    _do_fix_interrupted_tasks_status(db_engine)

    now = current_time()

    with make_session() as session:
        tasks_in_progress = (
            session.query(TaskJob)
            .filter(TaskJob.status.in_([TaskStatus.RUNNING.value, TaskStatus.PENDING.value]))
            .count()
        )
        assert tasks_in_progress == 0

        fixed_pending = session.get(TaskJob, "pending")
        assert fixed_pending.status == TaskStatus.FAILED.value
        assert fixed_pending.result_status is False
        assert fixed_pending.result_msg == "Task was interrupted due to server restart"
        assert (now - fixed_pending.completion_date).seconds <= 1

        fixed_running = session.get(TaskJob, "running")
        assert fixed_running.status == TaskStatus.FAILED.value
        assert fixed_running.result_status is False
        assert fixed_running.result_msg == "Task was interrupted due to server restart"
        assert (now - fixed_running.completion_date).seconds <= 1

        unchanged_completed = session.get(TaskJob, "completed")
        assert unchanged_completed.status == TaskStatus.COMPLETED.value
        assert unchanged_completed.result_status is True
        assert unchanged_completed.result_msg == "success"
        assert unchanged_completed.completion_date == datetime(2025, 6, 1, 12, 0, 0)

        unchanged_failed = session.get(TaskJob, "failed")
        assert unchanged_failed.status == TaskStatus.FAILED.value
        assert unchanged_failed.result_status is False
        assert unchanged_failed.result_msg == "failed"
        assert unchanged_failed.completion_date == datetime(2025, 6, 1, 12, 0, 0)

        unchanged_timeout = session.get(TaskJob, "timeout")
        assert unchanged_timeout.status == TaskStatus.TIMEOUT.value
        assert unchanged_timeout.result_status is False
        assert unchanged_timeout.result_msg == "timed out"
        assert unchanged_timeout.completion_date == datetime(2025, 6, 1, 12, 0, 0)

        unchanged_cancelled = session.get(TaskJob, "cancelled")
        assert unchanged_cancelled.status == TaskStatus.CANCELLED.value
        assert unchanged_cancelled.result_status is False
        assert unchanged_cancelled.result_msg == "was cancelled"
        assert unchanged_cancelled.completion_date == datetime(2025, 6, 1, 12, 0, 0)
