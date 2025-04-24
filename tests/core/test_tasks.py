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

import datetime
import time
import typing as t
from pathlib import Path
from unittest.mock import ANY, Mock

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import DummyEventBusService, EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.persistence import Base
from antarest.core.requests import UserHasNotPermissionError
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
from antarest.core.tasks.service import ITaskNotifier, TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService
from antarest.login.model import User
from antarest.login.utils import get_current_user
from antarest.service_creator import SESSION_ARGS
from antarest.study.model import RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import ThermalClusterTimeSeriesGeneratorTask
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand
from tests.helpers import with_admin_user, with_db_context
from tests.storage.test_service import build_study_service


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


@with_admin_user
@with_db_context
def test_service(core_config: Config, event_bus: IEventBus) -> None:
    engine = db.session.bind

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

    tasks = service.list_tasks(TaskListFilter())
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.FAILED
    assert tasks[0].creation_date_utc == str(creation_date)

    # Test Case: get task status
    # ==========================

    res = service.status_task("a")
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
        "progress": None,
    }
    assert res.model_dump() == expected

    # Test Case: add a task that fails and wait for it
    # ================================================

    # noinspection PyUnusedLocal
    def action_fail(notifier: ITaskNotifier) -> TaskResult:
        raise Exception("this action failed")

    failed_id = service.add_task(action_fail, "failed action", TaskType.COPY, None, None, None)
    service.await_task(failed_id, timeout_sec=2)

    failed_task = task_job_repo.get(failed_id)
    assert failed_task is not None
    assert failed_task.status == TaskStatus.FAILED.value
    assert failed_task.result_status is False
    assert failed_task.result_msg == "this action failed"
    assert failed_task.completion_date is not None

    # Test Case: add a task that succeeds and wait for it
    # ===================================================

    def action_ok(notifier: ITaskNotifier) -> TaskResult:
        notifier.notify_message("start")
        notifier.notify_message("end")
        return TaskResult(success=True, message="OK")

    ok_id = service.add_task(action_ok, None, TaskType.COPY, None, None, None)
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


@with_db_context
def test_repository() -> None:
    # Prepare two users in the database
    user1_id = 9
    db.session.add(User(id=user1_id, name="John"))
    user2_id = 10
    db.session.add(User(id=user2_id, name="Jane"))
    db.session.commit()

    # Create a RawStudy in the database
    study_id = "e34fe4d5-5964-4ef2-9baf-fad66dadc512"
    db.session.add(RawStudy(id=study_id, name="foo", version="860"))
    db.session.commit()

    # Create a TaskJobService
    task_job_repo = TaskJobRepository()

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

    assert len(db.session.query(TaskJobLog).where(TaskJobLog.task_id == new_task.id).all()) == 2

    task_job_repo.delete(new_task.id)
    assert len(db.session.query(TaskJobLog).where(TaskJobLog.task_id == new_task.id).all()) == 0
    assert task_job_repo.get(new_task.id) is None


@with_db_context
def test_cancel(core_config: Config, event_bus: IEventBus, admin_user: JWTUser) -> None:
    # Create a TaskJobService and add tasks
    task_job_repo = TaskJobRepository()
    task_job_repo.save(TaskJob(id="a", name="foo"))
    task_job_repo.save(TaskJob(id="b", name="foo"))

    # Create a TaskJobService
    service = TaskJobService(config=core_config, repository=task_job_repo, event_bus=event_bus)

    with pytest.raises(UserHasNotPermissionError):
        service.cancel_task("a")

    # The event_bus fixture is actually a EventBusService with LocalEventBus backend
    backend = t.cast(LocalEventBus, t.cast(EventBusService, event_bus).backend)

    # Test Case: cancel a task that is not in the service tasks map
    # =============================================================

    backend.clear_events()

    service.cancel_task("b", dispatch=True)

    collected_events = backend.get_events()

    assert len(collected_events) == 1
    assert collected_events[0].type == EventType.TASK_CANCEL_REQUEST
    assert collected_events[0].payload == "b"
    assert collected_events[0].permissions == PermissionInfo(public_mode=PublicMode.NONE)

    # Test Case: cancel a task that is in the service tasks map
    # =========================================================

    service.tasks["a"] = Mock(cancel=Mock(return_value=None))

    backend.clear_events()

    service.cancel_task("a", dispatch=True)

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


@with_db_context
def test_get_progress(admin_user: JWTUser, core_config: Config, event_bus: IEventBus) -> None:
    # Prepare two users in the database
    user1_id = 9
    db.session.add(User(id=user1_id, name="John"))
    user2_id = 10
    db.session.add(User(id=user2_id, name="Jane"))
    db.session.commit()

    # Create a RawStudy in the database
    study_id = "e34fe4d5-5964-4ef2-9baf-fad66dadc512"
    db.session.add(RawStudy(id=study_id, name="foo", version="860"))
    db.session.commit()

    # Create a TaskJobService
    task_job_repo = TaskJobRepository()

    # User 1 launches a ts generation
    first_task = TaskJob(
        name="ts_gen_1",
        owner_id=user1_id,
        type=TaskType.THERMAL_CLUSTER_SERIES_GENERATION,
        ref_id=study_id,
        progress=40,
    )
    first_task = task_job_repo.save(first_task)
    assert first_task.progress == 40
    assert first_task.ref_id == study_id

    # User 2 launches another generation
    second_task = TaskJob(
        name="ts_gen_2", owner_id=user2_id, ref_id=study_id, type=TaskType.THERMAL_CLUSTER_SERIES_GENERATION
    )
    second_task = task_job_repo.save(second_task)
    assert second_task.progress is None

    # Create a TaskJobService
    service = TaskJobService(config=core_config, repository=task_job_repo, event_bus=event_bus)

    # Asserts the progress cannot be fetched by users that didn't launch it
    user_2 = JWTUser(id=user2_id, type="user", impersonator=user2_id)
    for user in [None, user_2]:
        with pytest.raises(UserHasNotPermissionError):
            service.get_task_progress(first_task.id)

    # Asserts admin and user_1 can fetch the first_task progress
    user_1 = JWTUser(id=user1_id, type="user", impersonator=user1_id)
    for user in [user_1, admin_user]:
        progress = service.get_task_progress(first_task.id)
        assert progress == 40

    # Asserts admin and user_2 can fetch the second_task progress
    for user in [user_2, admin_user]:
        progress = service.get_task_progress(second_task.id)
        assert progress is None

    # Asserts fetching with a wrong id raises an Exception
    wrong_id = "foo_bar"
    with pytest.raises(HTTPException, match=f"Task {wrong_id} not found"):
        service.get_task_progress(wrong_id)


@with_admin_user
@with_db_context
def test_ts_generation_task(
    tmp_path: Path,
    core_config: Config,
    raw_study_service: RawStudyService,
) -> None:
    # =======================
    #  SET UP
    # =======================

    event_bus = DummyEventBusService()

    # Create a TaskJobService and add tasks
    task_job_repo = TaskJobRepository()

    # Create a TaskJobService
    task_job_service = TaskJobService(config=core_config, repository=task_job_repo, event_bus=event_bus)

    # Create a raw study
    raw_study_path = tmp_path / "study"

    regular_user = User(id=99, name="regular")
    db.session.add(regular_user)
    db.session.commit()

    raw_study = RawStudy(
        id="my_raw_study",
        name="my_raw_study",
        version="860",
        author="John Smith",
        created_at=datetime.datetime(2023, 7, 15, 16, 45),
        updated_at=datetime.datetime(2023, 7, 19, 8, 15),
        last_access=datetime.datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=regular_user,
        path=str(raw_study_path),
    )
    study_metadata_repository = StudyMetadataRepository(Mock(), None)
    db.session.add(raw_study)
    db.session.commit()

    # Set up the Raw Study
    raw_study_service.create(raw_study)
    # Create an area
    areas_path = raw_study_path / "input" / "areas"
    areas_path.mkdir(parents=True, exist_ok=True)
    (areas_path / "fr").mkdir(parents=True, exist_ok=True)
    (areas_path / "list.txt").touch(exist_ok=True)
    with open(areas_path / "list.txt", mode="w") as f:
        f.writelines(["fr"])
    # Create 2 thermal clusters
    thermal_path = raw_study_path / "input" / "thermal"
    thermal_path.mkdir(parents=True, exist_ok=True)
    fr_path = thermal_path / "clusters" / "fr"
    fr_path.mkdir(parents=True, exist_ok=True)
    (fr_path / "list.ini").touch(exist_ok=True)
    content = """
    [th_1]
name = th_1
nominalcapacity = 14.0

[th_2]
name = th_2
nominalcapacity = 14.0
"""
    (fr_path / "list.ini").write_text(content)
    # Create matrix files
    for th_name in ["th_1", "th_2"]:
        prepro_folder = thermal_path / "prepro" / "fr" / th_name
        prepro_folder.mkdir(parents=True, exist_ok=True)
        # Modulation
        modulation_df = pd.DataFrame(data=np.ones((8760, 3)))
        modulation_df.to_csv(prepro_folder / "modulation.txt", sep="\t", header=False, index=False)
        (prepro_folder / "data.txt").touch()
        # Data
        data_df = pd.DataFrame(data=np.zeros((365, 6)))
        data_df[0] = [1] * 365
        data_df[1] = [1] * 365
        data_df.to_csv(prepro_folder / "data.txt", sep="\t", header=False, index=False)
        # Series
        series_path = thermal_path / "series" / "fr" / th_name
        series_path.mkdir(parents=True, exist_ok=True)
        (series_path / "series.txt").touch()

    # Set up the mocks
    variant_study_service = Mock(spec=VariantStudyService)
    command_factory = Mock(spec=CommandFactory)
    variant_study_service.command_factory = command_factory
    command_factory.command_context = Mock(spec=CommandContext)
    config = Mock(spec=Config)

    study_service = build_study_service(
        raw_study_service,
        study_metadata_repository,
        config,
        task_service=task_job_service,
        event_bus=event_bus,
        variant_study_service=variant_study_service,
    )

    # =======================
    #  TEST CASE
    # =======================

    task = ThermalClusterTimeSeriesGeneratorTask(
        raw_study.id,
        repository=study_service.repository,
        storage_service=study_service.storage_service,
        event_bus=study_service.event_bus,
        study_interface_supplier=study_service.get_study_interface,
    )

    task_id = study_service.task_service.add_task(
        task,
        "test_generation",
        task_type=TaskType.THERMAL_CLUSTER_SERIES_GENERATION,
        ref_id=raw_study.id,
        progress=0,
        custom_event_messages=None,
    )

    # Await task
    study_service.task_service.await_task(task_id, 2)
    tasks = study_service.task_service.list_tasks(TaskListFilter())
    assert len(tasks) == 1
    task = tasks[0]
    assert task.ref_id == raw_study.id
    assert task.id == task_id
    assert task.name == "test_generation"
    assert task.status == TaskStatus.COMPLETED
    assert task.progress == 100

    # Check eventbus
    events = event_bus.events
    assert len(events) == 6
    assert events[0].type == EventType.TASK_ADDED
    assert events[1].type == EventType.TASK_RUNNING

    assert events[2].type == EventType.TASK_PROGRESS
    assert events[2].payload == {"task_id": task_id, "progress": 50}
    assert events[3].type == EventType.TASK_PROGRESS
    assert events[3].payload == {"task_id": task_id, "progress": 100}

    assert events[4].type == EventType.STUDY_EDITED
    assert events[5].type == EventType.TASK_COMPLETED


@with_db_context
def test_task_user(core_config: Config, event_bus: IEventBus):
    """
    Check if the user who submit a task is actually the owner of this task.
    """
    # Create a user who has no admin rights
    regular_user = User(id=99, name="regular")
    db.session.add(regular_user)

    # Define its token
    jwt_user = Mock(spec=JWTUser, id=regular_user.id, type="users", impersonator=regular_user.id)

    # Launch the task
    task_job_repository = TaskJobRepository()
    task_job_service = TaskJobService(config=core_config, repository=task_job_repository, event_bus=event_bus)

    # Newly created user initialize a task
    def action_task(notifier: ITaskNotifier) -> TaskResult:
        notifier.notify_message("start")

        # get current user
        current_user = get_current_user()

        notifier.notify_message("end")
        # must set the task 'result' field at regular_user.id
        return TaskResult(success=True, message="success", return_value=str(current_user.id))

    result = task_job_service.add_task(
        action=action_task,
        name="task_test_2",
        task_type=TaskType.SCAN,
        ref_id=None,
        progress=None,
        custom_event_messages=None,
    )

    task_job_service.await_task(result, 10)

    # Check whether the owner is the created user and not the admin one
    task_list = task_job_service.list_tasks(TaskListFilter())
    assert len(task_list) == 1
    assert task_list[0].owner != DEFAULT_ADMIN_USER.id
    assert task_list[0].owner == jwt_user.id
    assert task_list[0].result.return_value == str(jwt_user.id)
