import datetime
from pathlib import Path
import time
from typing import Callable, List
from unittest.mock import ANY, Mock, call

import pytest
from sqlalchemy import create_engine

from antarest.core.config import Config, RemoteWorkerConfig, TaskConfig
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.tasks.model import (
    TaskDTO,
    TaskJob,
    TaskJobLog,
    TaskListFilter,
    TaskResult,
    TaskStatus,
    TaskType,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand
from tests.conftest import with_db_context


def test_service() -> None:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    repo_mock = Mock(spec=TaskJobRepository)
    creation_date = datetime.datetime.utcnow()
    task = TaskJob(id="a", name="b", status=2, creation_date=creation_date)
    repo_mock.list.return_value = [task]
    repo_mock.get_or_raise.return_value = task
    service = TaskJobService(
        config=Config(), repository=repo_mock, event_bus=Mock()
    )
    repo_mock.save.assert_called_with(
        TaskJob(
            id="a",
            name="b",
            status=4,
            creation_date=creation_date,
            result_status=False,
            result_msg="Task was interrupted due to server restart",
            completion_date=ANY,
        )
    )

    tasks = service.list_tasks(
        TaskListFilter(),
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.FAILED
    assert tasks[0].creation_date_utc == str(creation_date)

    start = datetime.datetime.utcnow()
    end = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
    repo_mock.reset_mock()
    repo_mock.get.return_value = TaskJob(
        id="a",
        completion_date=end,
        name="Unnamed",
        owner_id=1,
        status=TaskStatus.COMPLETED.value,
        result_status=True,
        result_msg="OK",
        creation_date=start,
    )
    res = service.status_task("a", RequestParameters(user=DEFAULT_ADMIN_USER))
    assert res is not None
    assert res == TaskDTO(
        id="a",
        completion_date_utc=str(end),
        creation_date_utc=str(start),
        owner=1,
        name="Unnamed",
        result=TaskResult(success=True, message="OK"),
        status=TaskStatus.COMPLETED,
    )

    def action_fail(update_msg: Callable[[str], None]) -> TaskResult:
        raise NotImplementedError()

    def action_ok(update_msg: Callable[[str], None]) -> TaskResult:
        update_msg("start")
        update_msg("end")
        return TaskResult(success=True, message="OK")

    repo_mock.reset_mock()
    now = datetime.datetime.utcnow()
    task = TaskJob(
        name="failed action",
        owner_id=1,
        id="a",
        creation_date=now,
        status=TaskStatus.PENDING.value,
    )
    repo_mock.save.side_effect = lambda x: task
    repo_mock.get_or_raise.return_value = task
    service.add_task(
        action_fail,
        "failed action",
        None,
        None,
        None,
        RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.await_task("a")
    repo_mock.save.assert_has_calls(
        [
            call(
                TaskJob(
                    name="failed action",
                    owner_id=1,
                )
            ),
            # this is not called with that because the object is mutated, and mock seems to suck..
            # TaskJob(
            #     id="a",
            #     name="failed action",
            #     owner_id=1,
            #     status=TaskStatus.RUNNING.value,
            #     creation_date=now,
            # ),
            call(
                TaskJob(
                    id="a",
                    completion_date=ANY,
                    name="failed action",
                    owner_id=1,
                    status=TaskStatus.FAILED.value,
                    result_status=False,
                    result_msg="NotImplementedError()",
                    creation_date=now,
                )
            ),
            call(
                TaskJob(
                    id="a",
                    completion_date=ANY,
                    name="failed action",
                    owner_id=1,
                    status=TaskStatus.FAILED.value,
                    result_status=False,
                    result_msg="NotImplementedError()",
                    creation_date=now,
                )
            ),
        ]
    )

    repo_mock.reset_mock()
    now = datetime.datetime.utcnow()
    task = TaskJob(
        name="Unnamed",
        owner_id=1,
        id="a",
        creation_date=now,
        status=TaskStatus.PENDING.value,
    )
    repo_mock.save.side_effect = lambda x: task
    repo_mock.get_or_raise.return_value = task
    repo_mock.get.side_effect = [
        TaskJob(
            name="Unnamed",
            owner_id=1,
            id="a",
            creation_date=now,
            status=TaskStatus.RUNNING.value,
        ),
        TaskJob(
            name="Unnamed",
            owner_id=1,
            id="a",
            creation_date=now,
            status=TaskStatus.RUNNING.value,
        ),
    ]
    service.add_task(
        action_ok,
        None,
        None,
        None,
        None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.await_task("a")
    repo_mock.save.assert_has_calls(
        [
            call(TaskJob(owner_id=1, name="Unnamed")),
            # this is not called with that because the object is mutated, and mock seems to suck..
            # TaskJob(
            #     id="a",
            #     name="failed action",
            #     owner_id=1,
            #     status=TaskStatus.RUNNING.value,
            #     creation_date=now,
            # ),
            call(
                TaskJob(
                    id="a",
                    completion_date=ANY,
                    name="Unnamed",
                    owner_id=1,
                    status=TaskStatus.COMPLETED.value,
                    result_status=True,
                    result_msg="OK",
                    creation_date=now,
                )
            ),
            call(
                TaskJob(
                    name="Unnamed",
                    owner_id=1,
                    id="a",
                    creation_date=now,
                    status=TaskStatus.RUNNING.value,
                    logs=[TaskJobLog(message="start", task_id="a")],
                )
            ),
            call(
                TaskJob(
                    name="Unnamed",
                    owner_id=1,
                    id="a",
                    creation_date=now,
                    status=TaskStatus.RUNNING.value,
                    logs=[TaskJobLog(message="end", task_id="a")],
                )
            ),
            call(
                TaskJob(
                    id="a",
                    completion_date=ANY,
                    name="Unnamed",
                    owner_id=1,
                    status=TaskStatus.COMPLETED.value,
                    result_status=True,
                    result_msg="OK",
                    creation_date=now,
                )
            ),
        ]
    )

    repo_mock.get.reset_mock()
    repo_mock.get.side_effect = [None]
    service.await_task("elsewhere")
    repo_mock.get.assert_called_with("elsewhere")


class DummyWorker(AbstractWorker):
    def __init__(
        self, event_bus: IEventBus, accept: List[str], tmp_path: Path
    ):
        super().__init__("test", event_bus, accept)
        self.tmp_path = tmp_path

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        # simulate a "long" task ;-)
        time.sleep(0.01)
        relative_path = task_info.task_args["file"]
        (self.tmp_path / relative_path).touch()
        return TaskResult(success=True, message="")


@with_db_context
def test_worker_tasks(tmp_path: Path):
    repo_mock = Mock(spec=TaskJobRepository)
    repo_mock.list.return_value = []
    event_bus = EventBusService(LocalEventBus())
    service = TaskJobService(
        config=Config(
            tasks=TaskConfig(
                remote_workers=[
                    RemoteWorkerConfig(name="test", queues=["test"])
                ]
            )
        ),
        repository=repo_mock,
        event_bus=event_bus,
    )

    worker = DummyWorker(event_bus, ["test"], tmp_path)
    worker.start(threaded=True)

    file_to_create = "foo"

    assert not (tmp_path / file_to_create).exists()

    repo_mock.save.side_effect = [
        TaskJob(
            id="taskid",
            name="Unnamed",
            owner_id=0,
            type=TaskType.WORKER_TASK,
            ref_id=None,
        ),
        TaskJob(
            id="taskid",
            name="Unnamed",
            owner_id=0,
            type=TaskType.WORKER_TASK,
            ref_id=None,
            status=TaskStatus.RUNNING,
        ),
        TaskJob(
            id="taskid",
            name="Unnamed",
            owner_id=0,
            type=TaskType.WORKER_TASK,
            ref_id=None,
            status=TaskStatus.COMPLETED,
        ),
    ]
    repo_mock.get_or_raise.return_value = TaskJob(
        id="taskid",
        name="Unnamed",
        owner_id=0,
        type=TaskType.WORKER_TASK,
        ref_id=None,
    )
    task_id = service.add_worker_task(
        TaskType.WORKER_TASK,
        "test",
        {"file": file_to_create},
        None,
        None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.await_task(task_id)

    assert (tmp_path / file_to_create).exists()


def test_repository():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        task_repository = TaskJobRepository()

        new_task = TaskJob(name="foo", owner_id=0, type=TaskType.COPY)
        second_task = TaskJob(owner_id=1, ref_id="a")

        now = datetime.datetime.utcnow()
        new_task = task_repository.save(new_task)
        assert task_repository.get(new_task.id) == new_task
        assert new_task.status == TaskStatus.PENDING.value
        assert new_task.owner_id == 0
        assert new_task.creation_date >= now

        second_task = task_repository.save(second_task)

        result = task_repository.list(TaskListFilter(type=[TaskType.COPY]))
        assert len(result) == 1
        assert result[0].id == new_task.id

        result = task_repository.list(TaskListFilter(ref_id="a"))
        assert len(result) == 1
        assert result[0].id == second_task.id

        result = task_repository.list(TaskListFilter(), user=1)
        assert len(result) == 1
        assert result[0].id == second_task.id

        result = task_repository.list(TaskListFilter())
        assert len(result) == 2

        result = task_repository.list(TaskListFilter(name="fo"))
        assert len(result) == 1

        result = task_repository.list(
            TaskListFilter(name="fo", status=[TaskStatus.RUNNING])
        )
        assert len(result) == 0
        new_task.status = TaskStatus.RUNNING.value
        task_repository.save(new_task)
        result = task_repository.list(
            TaskListFilter(name="fo", status=[TaskStatus.RUNNING])
        )
        assert len(result) == 1

        new_task.completion_date = datetime.datetime.utcnow()
        task_repository.save(new_task)
        result = task_repository.list(
            TaskListFilter(
                name="fo",
                from_completion_date_utc=(
                    new_task.completion_date + datetime.timedelta(seconds=1)
                ).timestamp(),
            )
        )
        assert len(result) == 0
        result = task_repository.list(
            TaskListFilter(
                name="fo",
                from_completion_date_utc=(
                    new_task.completion_date - datetime.timedelta(seconds=1)
                ).timestamp(),
            )
        )
        assert len(result) == 1

        new_task.logs.append(TaskJobLog(message="hello"))
        new_task.logs.append(TaskJobLog(message="bar"))
        task_repository.save(new_task)
        new_task = task_repository.get(new_task.id)
        assert len(new_task.logs) == 2
        assert new_task.logs[0].message == "hello"

        assert (
            len(
                db.session.query(TaskJobLog)
                .where(TaskJobLog.task_id == new_task.id)
                .all()
            )
            == 2
        )

        task_repository.delete(new_task.id)
        assert (
            len(
                db.session.query(TaskJobLog)
                .where(TaskJobLog.task_id == new_task.id)
                .all()
            )
            == 0
        )
        assert task_repository.get(new_task.id) is None


def test_cancel():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    repo_mock = Mock(spec=TaskJobRepository)
    repo_mock.list.return_value = []
    service = TaskJobService(
        config=Config(), repository=repo_mock, event_bus=Mock()
    )

    with pytest.raises(UserHasNotPermissionError):
        service.cancel_task("a", RequestParameters())

    service.cancel_task(
        "b", RequestParameters(user=DEFAULT_ADMIN_USER), dispatch=True
    )
    service.event_bus.push.assert_called_with(
        Event(
            type=EventType.TASK_CANCEL_REQUEST,
            payload="b",
            permissions=PermissionInfo(public_mode=PublicMode.NONE),
        )
    )

    creation_date = datetime.datetime.utcnow()
    task = TaskJob(id="a", name="b", status=2, creation_date=creation_date)
    repo_mock.list.return_value = [task]
    repo_mock.get_or_raise.return_value = task
    service.tasks["a"] = Mock()
    service.cancel_task(
        "a", RequestParameters(user=DEFAULT_ADMIN_USER), dispatch=True
    )
    task.status = TaskStatus.CANCELLED.value
    repo_mock.save.assert_called_with(task)
