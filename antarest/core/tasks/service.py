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
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from http import HTTPStatus
from typing import Awaitable, Callable, Dict, List, Optional, TypeAlias

from fastapi import HTTPException
from sqlalchemy.orm import Session  # type: ignore
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType, IEventBus
from antarest.core.jwt import JWTUser
from antarest.core.logging.utils import task_context
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import MustBeAuthenticatedError, UserHasNotPermissionError
from antarest.core.tasks.model import (
    CustomTaskEventMessages,
    TaskDTO,
    TaskEventPayload,
    TaskJob,
    TaskJobLog,
    TaskListFilter,
    TaskResult,
    TaskStatus,
    TaskType,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import retry
from antarest.login.utils import get_current_user
from antarest.worker.worker import WorkerTaskCommand, WorkerTaskResult

logger = logging.getLogger(__name__)

DEFAULT_AWAIT_MAX_TIMEOUT = 172800  # 48 hours
"""Default timeout for `await_task` in seconds."""


class ITaskNotifier(ABC):
    @abstractmethod
    def notify_message(self, message: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def notify_progress(self, progress: int) -> None:
        raise NotImplementedError()


Task: TypeAlias = Callable[[ITaskNotifier], TaskResult]


class ITaskService(ABC):
    @abstractmethod
    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: Dict[str, int | float | bool | str],
        name: Optional[str],
        ref_id: Optional[str],
    ) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def add_task(
        self,
        action: Task,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        progress: Optional[int],
        custom_event_messages: Optional[CustomTaskEventMessages],
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        raise NotImplementedError()

    @abstractmethod
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        raise NotImplementedError()

    @abstractmethod
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        raise NotImplementedError()


# noinspection PyUnusedLocal
class NoopNotifier(ITaskNotifier):
    """This class is used in tasks when no notification is required."""

    @override
    def notify_message(self, message: str) -> None:
        return

    @override
    def notify_progress(self, progress: int) -> None:
        return


class TaskLogAndProgressRecorder(ITaskNotifier):
    """
    Callback used to register log messages in the TaskJob table.

    Args:
        task_id: The task id.
        session: The database session created in the same thread as the task thread.
    """

    def __init__(self, task_id: str, session: Session, event_bus: IEventBus) -> None:
        self.session = session
        self.task_id = task_id
        self.event_bus = event_bus

    @override
    def notify_message(self, message: str) -> None:
        task = self.session.query(TaskJob).get(self.task_id)
        if task:
            task.logs.append(TaskJobLog(message=message, task_id=self.task_id))
            self.session.commit()

    @override
    def notify_progress(self, progress: int) -> None:
        self.session.query(TaskJob).filter(TaskJob.id == self.task_id).update({TaskJob.progress: progress})
        self.session.commit()

        self.event_bus.push(
            Event(
                type=EventType.TASK_PROGRESS,
                payload={
                    "task_id": self.task_id,
                    "progress": progress,
                },
                permissions=PermissionInfo(public_mode=PublicMode.READ),
                channel=EventChannelDirectory.TASK + self.task_id,
            )
        )


class TaskJobService(ITaskService):
    def __init__(
        self,
        config: Config,
        repository: TaskJobRepository,
        event_bus: IEventBus,
    ):
        self.config = config
        self.repo = repository
        self.event_bus = event_bus
        self.tasks: Dict[str, Future[None]] = {}
        self.threadpool = ThreadPoolExecutor(max_workers=config.tasks.max_workers, thread_name_prefix="taskjob_")
        self.event_bus.add_listener(self.create_task_event_callback(), [EventType.TASK_CANCEL_REQUEST])
        self.remote_workers = config.tasks.remote_workers

    def _create_worker_task(
        self,
        task_id: str,
        task_type: str,
        task_args: Dict[str, int | float | bool | str],
    ) -> Task:
        task_result_wrapper: List[TaskResult] = []

        def _create_awaiter(
            res_wrapper: List[TaskResult],
        ) -> Callable[[Event], Awaitable[None]]:
            async def _await_task_end(event: Event) -> None:
                task_event = WorkerTaskResult.model_validate(event.payload)
                if task_event.task_id == task_id:
                    res_wrapper.append(task_event.task_result)

            return _await_task_end

        # noinspection PyUnusedLocal
        def _send_worker_task(logger_: ITaskNotifier) -> TaskResult:
            listener_id = self.event_bus.add_listener(
                _create_awaiter(task_result_wrapper),
                [EventType.WORKER_TASK_ENDED],
            )
            self.event_bus.queue(
                Event(
                    type=EventType.WORKER_TASK,
                    payload=WorkerTaskCommand(
                        task_id=task_id,
                        task_type=task_type,
                        task_args=task_args,
                    ),
                    # Use `NONE` for internal events
                    permissions=PermissionInfo(public_mode=PublicMode.NONE),
                ),
                task_type,
            )
            while not task_result_wrapper:
                logger.info("💤 Sleeping 1 second...")
                time.sleep(1)
            self.event_bus.remove_listener(listener_id)
            return task_result_wrapper[0]

        return _send_worker_task

    def check_remote_worker_for_queue(self, task_queue: str) -> bool:
        return any(task_queue in rw.queues for rw in self.remote_workers)

    @override
    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: Dict[str, int | float | bool | str],
        name: Optional[str],
        ref_id: Optional[str],
    ) -> Optional[str]:
        if not self.check_remote_worker_for_queue(task_queue):
            logger.warning(f"Failed to find configured remote worker for task queue {task_queue}")
            return None

        task = self._create_task(name, task_type, ref_id, None)
        self._launch_task(self._create_worker_task(str(task.id), task_queue, task_args), task, None)
        return str(task.id)

    @override
    def add_task(
        self,
        action: Task,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        progress: Optional[int],
        custom_event_messages: Optional[CustomTaskEventMessages],
    ) -> str:
        task = self._create_task(name, task_type, ref_id, progress)
        self._launch_task(action, task, custom_event_messages)
        return str(task.id)

    def _create_task(
        self,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        progress: Optional[int],
    ) -> TaskJob:
        user = get_current_user()
        if not user:
            raise MustBeAuthenticatedError()

        return self.repo.save(
            TaskJob(
                name=name or "Unnamed",
                owner_id=user.impersonator,
                type=task_type,
                ref_id=ref_id,
                progress=progress,
            )
        )

    def _launch_task(
        self,
        action: Task,
        task: TaskJob,
        custom_event_messages: Optional[CustomTaskEventMessages],
    ) -> None:
        user = get_current_user()
        if not user:
            raise MustBeAuthenticatedError()

        self.event_bus.push(
            Event(
                type=EventType.TASK_ADDED,
                payload=TaskEventPayload(
                    id=task.id,
                    message=(
                        custom_event_messages.start if custom_event_messages is not None else f"Task {task.id} added"
                    ),
                    type=task.type,
                    study_id=task.ref_id,
                ).model_dump(),
                permissions=PermissionInfo(owner=user.impersonator),
            )
        )
        future = self.threadpool.submit(self._run_task, action, task.id, user, custom_event_messages)
        self.tasks[task.id] = future

    def create_task_event_callback(self) -> Callable[[Event], Awaitable[None]]:
        async def task_event_callback(event: Event) -> None:
            self._cancel_task(str(event.payload), dispatch=False)

        return task_event_callback

    def cancel_task(self, task_id: str, dispatch: bool = False) -> None:
        task = self.repo.get_or_raise(task_id)
        user = get_current_user()
        if user and (user.is_site_admin() or task.owner_id == user.impersonator):
            self._cancel_task(task_id, dispatch)
        else:
            raise UserHasNotPermissionError()

    def _cancel_task(self, task_id: str, dispatch: bool = False) -> None:
        task = self.repo.get_or_raise(task_id)
        if task_id in self.tasks:
            self.tasks[task_id].cancel()
            task.status = TaskStatus.CANCELLED.value
            self.repo.save(task)
        elif dispatch:
            self.event_bus.push(
                Event(
                    type=EventType.TASK_CANCEL_REQUEST,
                    payload=task_id,
                    # Use `NONE` for internal events
                    permissions=PermissionInfo(public_mode=PublicMode.NONE),
                )
            )

    @override
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        user = get_current_user()
        if not user:
            raise MustBeAuthenticatedError()
        if task := self.repo.get(task_id):
            return task.to_dto(with_logs)
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Failed to retrieve task {task_id} in db",
            )

    @override
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        return [task.to_dto() for task in self.list_db_tasks(task_filter)]

    def list_db_tasks(self, task_filter: TaskListFilter) -> List[TaskJob]:
        current_user = get_current_user()
        if not current_user:
            raise MustBeAuthenticatedError()
        user = None if current_user.is_site_admin() else current_user.impersonator
        return self.repo.list(task_filter, user)

    @override
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        if task_id in self.tasks:
            try:
                logger.info(f"🤔 Awaiting task '{task_id}' {timeout_sec}s...")
                self.tasks[task_id].result(timeout_sec)
                logger.info(f"📌 Task '{task_id}' done.")
            except Exception as exc:
                logger.critical(f"🤕 Task '{task_id}' failed: {exc}.")
                raise
        else:
            logger.warning(f"Task '{task_id}' not handled by this worker, will poll for task completion from db")
            end = time.time() + timeout_sec
            while time.time() < end:
                task_status = db.session.query(TaskJob.status).filter(TaskJob.id == task_id).scalar()
                if task_status is None:
                    logger.error(f"Awaited task '{task_id}' was not found")
                    return
                if TaskStatus(task_status).is_final():
                    return
                logger.info("💤 Sleeping 2 seconds...")
                time.sleep(2)

            logger.error(f"Timeout while awaiting task '{task_id}'")
            db.session.query(TaskJob).filter(TaskJob.id == task_id).update(
                {
                    TaskJob.status: TaskStatus.TIMEOUT.value,
                    TaskJob.result_msg: f"Task '{task_id}' timeout after {timeout_sec} seconds",
                    TaskJob.result_status: False,
                }
            )
            db.session.commit()

    def _run_task(
        self,
        callback: Task,
        task_id: str,
        jwt_user: JWTUser,
        custom_event_messages: Optional[CustomTaskEventMessages] = None,
    ) -> None:
        # We need to catch all exceptions so that the calling thread is guaranteed
        # to not die
        try:
            # attention: this function is executed in a thread, not in the main process
            with task_context(task_id=task_id, user=jwt_user):
                with db():
                    # Important to keep this retry for now,
                    # in case commit is not visible (read from replica ...)
                    task = retry(lambda: self.repo.get_or_raise(task_id))
                    task_type = task.type
                    study_id = task.ref_id

                self.event_bus.push(
                    Event(
                        type=EventType.TASK_RUNNING,
                        payload=TaskEventPayload(
                            id=task_id,
                            message=(
                                custom_event_messages.running
                                if custom_event_messages is not None
                                else f"Task {task_id} is running"
                            ),
                            type=task_type,
                            study_id=study_id,
                        ).model_dump(),
                        permissions=PermissionInfo(public_mode=PublicMode.READ),
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )

                logger.info(f"Starting task {task_id}")
                with db():
                    db.session.query(TaskJob).filter(TaskJob.id == task_id).update(
                        {TaskJob.status: TaskStatus.RUNNING.value}
                    )
                    db.session.commit()
                logger.info(f"Task {task_id} set to RUNNING")

                with db():
                    # We must use the DB session attached to the current thread
                    result = callback(TaskLogAndProgressRecorder(task_id, db.session, self.event_bus))

                status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                logger.info(f"Task {task_id} ended with status {status}")

                with db():
                    # Do not use the `timezone.utc` timezone to preserve a naive datetime.
                    completion_date = datetime.datetime.utcnow() if status.is_final() else None
                    db.session.query(TaskJob).filter(TaskJob.id == task_id).update(
                        {
                            TaskJob.status: status.value,
                            TaskJob.result_msg: result.message,
                            TaskJob.result_status: result.success,
                            TaskJob.result: result.return_value,
                            TaskJob.completion_date: completion_date,
                        }
                    )
                    db.session.commit()

                event_type = {True: EventType.TASK_COMPLETED, False: EventType.TASK_FAILED}[result.success]
                event_msg = {True: "completed", False: "failed"}[result.success]
                self.event_bus.push(
                    Event(
                        type=event_type,
                        payload=TaskEventPayload(
                            id=task_id,
                            message=(
                                custom_event_messages.end
                                if custom_event_messages is not None
                                else f"Task {task_id} {event_msg}"
                            ),
                            type=task_type,
                            study_id=study_id,
                        ).model_dump(),
                        permissions=PermissionInfo(public_mode=PublicMode.READ),
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )
        except Exception as exc:
            err_msg = f"Task {task_id} failed: Unhandled exception {exc}"
            logger.error(err_msg, exc_info=exc)

            try:
                with db():
                    db.session.query(TaskJob).filter(TaskJob.id == task_id).update(
                        {
                            TaskJob.status: TaskStatus.FAILED.value,
                            TaskJob.result_msg: str(exc),
                            TaskJob.result_status: False,
                            TaskJob.completion_date: datetime.datetime.utcnow(),
                        }
                    )
                    db.session.commit()

                message = err_msg if custom_event_messages is None else custom_event_messages.end
                self.event_bus.push(
                    Event(
                        type=EventType.TASK_FAILED,
                        payload=TaskEventPayload(
                            id=task_id, message=message, type=task_type, study_id=study_id
                        ).model_dump(),
                        permissions=PermissionInfo(public_mode=PublicMode.READ),
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )
            except Exception as inner_exc:
                logger.error(
                    f"An exception occurred while handling execution error of task {task_id}: {inner_exc}",
                    exc_info=inner_exc,
                )

    def get_task_progress(self, task_id: str) -> Optional[int]:
        task = self.repo.get_or_raise(task_id)
        user = get_current_user()
        if user and (user.is_site_admin() or user.is_admin_token() or task.owner_id == user.impersonator):
            return task.progress
        else:
            raise UserHasNotPermissionError()
