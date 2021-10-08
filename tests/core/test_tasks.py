import datetime
from typing import Callable
from unittest.mock import Mock, ANY, call

from sqlalchemy import create_engine

from antarest.core.config import Config
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import (
    TaskJob,
    TaskStatus,
    TaskListFilter,
    TaskJobLog,
    TaskResult,
    TaskDTO,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db


def test_service() -> TaskJobService:
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
    assert tasks[0].creation_date_utc == creation_date.timestamp()

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
        completion_date_utc=end.timestamp(),
        creation_date_utc=start.timestamp(),
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
                    result_msg="",
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
                    result_msg="",
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

    return service


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

        new_task = TaskJob(name="foo", owner_id=0)
        second_task = TaskJob(owner_id=1)

        now = datetime.datetime.utcnow()
        new_task = task_repository.save(new_task)
        assert task_repository.get(new_task.id) == new_task
        assert new_task.status == TaskStatus.PENDING.value
        assert new_task.owner_id == 0
        assert new_task.creation_date >= now

        second_task = task_repository.save(second_task)

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