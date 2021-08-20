import datetime
from typing import Callable
from unittest.mock import Mock, ANY, call

import pytest
from sqlalchemy import create_engine

from antarest.core.config import Config, SecurityConfig
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
from antarest.login.model import Password, User
from antarest.login.repository import UserRepository
from antarest.study.storage.variantstudy.model.db.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyCommandRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


def test_service() -> VariantStudyService:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    repo_mock = Mock(spec=VariantStudyCommandRepository)
    creation_date = datetime.datetime.utcnow()
    repo_mock.create.return_value = [
        VariantStudy(id="a", name="b", snapshot=None, commands=[])
    ]
    service = VariantStudyService(
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


def test_repository():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        variant_repository = VariantStudyCommandRepository()

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