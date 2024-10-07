# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import datetime
import time
import typing as t
from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import Session, sessionmaker  # type: ignore

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.tasks.model import (
    TaskJob,
    TaskJobLog,
    TaskListFilter,
    TaskResult,
    TaskStatus,
    TaskType,
    cancel_orphan_tasks,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService
from antarest.login.model import User
from antarest.login.repository import UserRepository
from antarest.service_creator import SESSION_ARGS
from antarest.study.model import RawStudy
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand
from tests.helpers import with_db_context


@pytest.fixture(name="db_engine", autouse=True)
def db_engine_fixture(tmp_path: Path) -> t.Generator[Engine, None, None]:
    """
    Fixture that creates an SQLite database in a temporary directory.

    When a function runs in a different thread than the main one and needs to use
    the database, it uses the global `db` object. This object helps create a new
    local session in the thread to connect to the SQLite database.
    However, we can't use an in-memory SQLite database ("sqlite:///:memory:") because
    it creates a new empty database each time. That's why we use a SQLite database stored on disk.

    Yields:
        An instance of the created SQLite database engine.
    """
    db_path = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    engine.execute("PRAGMA foreign_keys = ON")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@with_db_context
def test_service(core_config: Config, event_bus: IEventBus) -> None:
    engine = db.session.bind

    user_repo = UserRepository(session=db.session)
    user_repo.save(User(id=DEFAULT_ADMIN_USER.id))

    task_job_repo = TaskJobRepository()

    # Prepare a TaskJob in the database
    creation_date = datetime.datetime.utcnow()
    running_task = TaskJob(id="a", name="b", status=TaskStatus.RUNNING.value, creation_date=creation_date)
    task_job_repo.save(running_task)

    # Create a TaskJobService
    service = TaskJobService(config=core_config, repository=task_job_repo, event_bus=event_bus)

    # Cancel pending and running tasks
    cancel_orphan_tasks(engine=engine, session_args=SESSION_ARGS)

    # Test Case: list tasks
    # =====================

    tasks = service.list_tasks(
        TaskListFilter(),
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.FAILED
    assert tasks[0].creation_date_utc == str(creation_date)

    # Test Case: get task status
    # ==========================

    res = service.status_task("a", RequestParameters(user=DEFAULT_ADMIN_USER))
    assert res is not None
    expected = {
        "completion_date_utc": ANY,
        "creation_date_utc": creation_date.isoformat(" "),
        "id": "a",
        "logs": None,
        "name": "b",
        "owner": None,
        "ref_id": None,
        "result": {
            "message": "Task was interrupted due to server restart",
            "return_value": None,
            "success": False,
        },
        "status": TaskStatus.FAILED,
        "type": None,
    }
    assert res.model_dump() == expected

    # Test Case: add a task that fails and wait for it
    # ================================================

    # noinspection PyUnusedLocal
    def action_fail(update_msg: t.Callable[[str], None]) -> TaskResult:
        raise Exception("this action failed")

    failed_id = service.add_task(
        action_fail,
        "failed action",
        None,
        None,
        None,
        RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.await_task(failed_id, timeout_sec=2)

    failed_task = task_job_repo.get(failed_id)
    assert failed_task is not None
    assert failed_task.status == TaskStatus.FAILED.value
    assert failed_task.result_status is False
    assert failed_task.result_msg == (
        f"Task {failed_id} failed: Unhandled exception this action failed"
        f"\nSee the logs for detailed information and the error traceback."
    )
    assert failed_task.completion_date is not None

    # Test Case: add a task that succeeds and wait for it
    # ===================================================

    def action_ok(update_msg: t.Callable[[str], None]) -> TaskResult:
        update_msg("start")
        update_msg("end")
        return TaskResult(success=True, message="OK")

    ok_id = service.add_task(
        action_ok,
        None,
        None,
        None,
        None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.await_task(ok_id, timeout_sec=2)

    ok_task = task_job_repo.get(ok_id)
    assert ok_task is not None
    assert ok_task.status == TaskStatus.COMPLETED.value
    assert ok_task.result_status is True
    assert ok_task.result_msg == "OK"
    assert ok_task.completion_date is not None
    assert len(ok_task.logs) == 2
    assert ok_task.logs[0].message == "start"
    assert ok_task.logs[1].message == "end"


class DummyWorker(AbstractWorker):
    def __init__(self, event_bus: IEventBus, accept: t.List[str], tmp_path: Path):
        super().__init__("test", event_bus, accept)
        self.tmp_path = tmp_path

    def _execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        # simulate a "long" task ;-)
        time.sleep(0.01)
        relative_path = t.cast(str, task_info.task_args["file"])
        (self.tmp_path / relative_path).touch()
        return TaskResult(success=True, message="")


def test_repository(db_session: Session) -> None:
    # Prepare two users in the database
    user1_id = 9
    db_session.add(User(id=user1_id, name="John"))
    user2_id = 10
    db_session.add(User(id=user2_id, name="Jane"))
    db_session.commit()

    # Create a RawStudy in the database
    study_id = "e34fe4d5-5964-4ef2-9baf-fad66dadc512"
    db_session.add(RawStudy(id=study_id, name="foo", version="860"))
    db_session.commit()

    # Create a TaskJobService
    task_job_repo = TaskJobRepository(db_session)

    new_task = TaskJob(name="foo", owner_id=user1_id, type=TaskType.COPY)

    now = datetime.datetime.utcnow()
    new_task = task_job_repo.save(new_task)
    assert task_job_repo.get(new_task.id) == new_task
    assert new_task.status == TaskStatus.PENDING.value
    assert new_task.owner_id == user1_id
    assert new_task.creation_date >= now

    second_task = TaskJob(name="bar", owner_id=user2_id, ref_id=study_id)
    second_task = task_job_repo.save(second_task)

    result = task_job_repo.list(TaskListFilter(type=[TaskType.COPY]))
    assert len(result) == 1
    assert result[0].id == new_task.id

    result = task_job_repo.list(TaskListFilter(ref_id=study_id))
    assert len(result) == 1
    assert result[0].id == second_task.id

    result = task_job_repo.list(TaskListFilter(), user=user2_id)
    assert len(result) == 1
    assert result[0].id == second_task.id

    result = task_job_repo.list(TaskListFilter())
    assert len(result) == 2

    result = task_job_repo.list(TaskListFilter(name="fo"))
    assert len(result) == 1

    result = task_job_repo.list(TaskListFilter(name="fo", status=[TaskStatus.RUNNING]))
    assert len(result) == 0
    new_task.status = TaskStatus.RUNNING.value
    task_job_repo.save(new_task)
    result = task_job_repo.list(TaskListFilter(name="fo", status=[TaskStatus.RUNNING]))
    assert len(result) == 1

    new_task.completion_date = datetime.datetime.utcnow()
    task_job_repo.save(new_task)
    result = task_job_repo.list(
        TaskListFilter(
            name="fo",
            from_completion_date_utc=(new_task.completion_date + datetime.timedelta(seconds=1)).timestamp(),
        )
    )
    assert len(result) == 0
    result = task_job_repo.list(
        TaskListFilter(
            name="fo",
            from_completion_date_utc=(new_task.completion_date - datetime.timedelta(seconds=1)).timestamp(),
        )
    )
    assert len(result) == 1

    new_task.logs.append(TaskJobLog(message="hello"))
    new_task.logs.append(TaskJobLog(message="bar"))
    task_job_repo.save(new_task)
    assert new_task.id is not None
    new_task = task_job_repo.get_or_raise(new_task.id)
    assert len(new_task.logs) == 2
    assert new_task.logs[0].message == "hello"

    assert len(db_session.query(TaskJobLog).where(TaskJobLog.task_id == new_task.id).all()) == 2

    task_job_repo.delete(new_task.id)
    assert len(db_session.query(TaskJobLog).where(TaskJobLog.task_id == new_task.id).all()) == 0
    assert task_job_repo.get(new_task.id) is None


@with_db_context
def test_cancel(core_config: Config, event_bus: IEventBus) -> None:
    # Create a TaskJobService and add tasks
    task_job_repo = TaskJobRepository()
    task_job_repo.save(TaskJob(id="a", name="foo"))
    task_job_repo.save(TaskJob(id="b", name="foo"))

    # Create a TaskJobService
    service = TaskJobService(config=core_config, repository=task_job_repo, event_bus=event_bus)

    with pytest.raises(UserHasNotPermissionError):
        service.cancel_task("a", RequestParameters())

    # The event_bus fixture is actually a EventBusService with LocalEventBus backend
    backend = t.cast(LocalEventBus, t.cast(EventBusService, event_bus).backend)

    # Test Case: cancel a task that is not in the service tasks map
    # =============================================================

    backend.clear_events()

    service.cancel_task("b", RequestParameters(user=DEFAULT_ADMIN_USER), dispatch=True)

    collected_events = backend.get_events()

    assert len(collected_events) == 1
    assert collected_events[0].type == EventType.TASK_CANCEL_REQUEST
    assert collected_events[0].payload == "b"
    assert collected_events[0].permissions == PermissionInfo(public_mode=PublicMode.NONE)

    # Test Case: cancel a task that is in the service tasks map
    # =========================================================

    service.tasks["a"] = Mock(cancel=Mock(return_value=None))

    backend.clear_events()

    service.cancel_task("a", RequestParameters(user=DEFAULT_ADMIN_USER), dispatch=True)

    collected_events = backend.get_events()
    assert len(collected_events) == 0, "No event should have been emitted because the task is in the service map"
    task_a = task_job_repo.get("a")
    assert task_a is not None
    assert task_a.status == TaskStatus.CANCELLED.value


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
def test_cancel_orphan_tasks(
    db_engine: Engine,
    status: int,
    result_status: bool,
    result_msg: str,
) -> None:
    max_diff_seconds: int = 1
    test_id: str = "2ea94758-9ea5-4015-a45f-b245a6ffc147"

    completion_date: datetime.datetime = datetime.datetime.utcnow()
    task_job = TaskJob(
        id=test_id,
        name="test",
        status=status,
        result_status=result_status,
        result_msg=result_msg,
        completion_date=completion_date,
    )
    make_session = sessionmaker(bind=db_engine, **SESSION_ARGS)
    with make_session() as session:
        session.add(task_job)
        session.commit()
    cancel_orphan_tasks(engine=db_engine, session_args=SESSION_ARGS)
    with make_session() as session:
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
            assert (datetime.datetime.utcnow() - updated_task_job.completion_date).seconds <= max_diff_seconds
        else:
            updated_task_job = session.query(TaskJob).get(test_id)
            assert updated_task_job.status == status
            assert updated_task_job.result_status == result_status
            assert updated_task_job.result_msg == result_msg
            assert (datetime.datetime.utcnow() - updated_task_job.completion_date).seconds <= max_diff_seconds
