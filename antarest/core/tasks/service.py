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
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from http import HTTPStatus
from typing import TypeAlias

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType, IEventBus
from antarest.core.jwt import JWTUser
from antarest.core.logging.utils import task_context
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import UserHasNotPermissionError
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
from antarest.core.utils.utils import current_time, retry
from antarest.login.utils import get_current_user, require_current_user

logger = logging.getLogger(__name__)

DEFAULT_AWAIT_MAX_TIMEOUT = 172800  # 48 hours
"""Default timeout for `await_task` in seconds."""


class TaskNotFoundError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=detail)


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
    def add_task(
        self,
        action: Task,
        name: str | None,
        task_type: TaskType,
        ref_id: str | None,
        progress: int | None,
        custom_event_messages: CustomTaskEventMessages | None,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        """
        Retrieves information about a task.

        Raise:
            TaskNotFoundError: if the task is not found in the database.
        """
        raise NotImplementedError()

    @abstractmethod
    def list_tasks(self, task_filter: TaskListFilter) -> list[TaskDTO]:
        raise NotImplementedError()

    @abstractmethod
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        """
        Waits for the completion of task for the specified time.

        Raises:
            TimeoutError: if the task is not completed before the timeout
        """
        raise NotImplementedError()

    @abstractmethod
    def cancel_task(self, task_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_task_progress(self, task_id: str) -> int | None:
        raise NotImplementedError()

    @abstractmethod
    def delete_task_by_creation_date(self, task_retention_duration: int) -> int:
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
        task = self.session.get(TaskJob, self.task_id)
        if task:
            task.logs.append(TaskJobLog(message=message, task_id=self.task_id))
            self.session.commit()

    @override
    def notify_progress(self, progress: int) -> None:
        stmt = update(TaskJob).where(TaskJob.id == self.task_id).values(progress=progress)
        self.session.execute(stmt)
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


class TaskServiceListener(ABC):
    """
    Allows to observe tasks lifecycle.

    There are 2 alternative flows of operation:

     - the standard flow is submit -> start -> end.
     - If a task is cancelled before it starts executing, the flow will be
       submit -> cancel.
    """

    @abstractmethod
    def on_task_submit(self, task_id: str, task_type: TaskType) -> None:
        """
        Called as soon as a new task has been submitted for execution.
        """

    @abstractmethod
    def on_task_start(self, task_id: str, task_type: TaskType) -> None:
        """
        Called when a task is actually started.

        At that point, it is guaranteed that:
          - the listener will also be notified of the end of the task
          - the task cannot be cancelled anymore
        """

    @abstractmethod
    def on_task_cancel(self, task_id: str, task_type: TaskType) -> None:
        """
        Called when a task is actually cancelled, which means it has not started.
        """

    @abstractmethod
    def on_task_end(self, task_id: str, task_type: TaskType, task_status: TaskStatus) -> None:
        """
        Called when a started task completes, either successfully or not.
        """


class TaskJobService(ITaskService):
    def __init__(
        self,
        config: Config,
        repository: TaskJobRepository,
        event_bus: IEventBus,
        listeners: Sequence[TaskServiceListener] | None = None,
    ):
        self.repo = repository
        self.event_bus = event_bus
        self.tasks: dict[str, Future[None]] = {}
        self.threadpool = ThreadPoolExecutor(max_workers=config.tasks.max_workers, thread_name_prefix="taskjob_")
        self.event_bus.add_listener(self.create_task_event_callback(), [EventType.TASK_CANCEL_REQUEST])
        self._listeners = list(listeners) if listeners else []

    @override
    def add_task(
        self,
        action: Task,
        name: str | None,
        task_type: TaskType,
        ref_id: str | None,
        progress: int | None,
        custom_event_messages: CustomTaskEventMessages | None,
    ) -> str:
        task = self._create_task(name, task_type, ref_id, progress)
        self._launch_task(action, task, custom_event_messages)
        return str(task.id)

    def _create_task(
        self,
        name: str | None,
        task_type: TaskType | None,
        ref_id: str | None,
        progress: int | None,
    ) -> TaskJob:
        user = require_current_user()
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
        custom_event_messages: CustomTaskEventMessages | None,
    ) -> None:
        user = require_current_user()

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

        for listener in self._listeners:
            listener.on_task_submit(task.id, task_type=task.get_type())

        future = self.threadpool.submit(self._run_task, action, task.id, task.get_type(), user, custom_event_messages)
        self.tasks[task.id] = future

    def create_task_event_callback(self) -> Callable[[Event], Awaitable[None]]:
        async def task_event_callback(event: Event) -> None:
            self._do_cancel_task(str(event.payload))

        return task_event_callback

    @override
    def cancel_task(self, task_id: str) -> None:
        task = self.repo.get_or_raise(task_id)
        user = require_current_user()
        if user.is_site_admin() or task.owner_id == user.impersonator:
            # Since the task may be executed in another worker,
            # we need to send a request to cancel it.
            self._request_cancel(task_id)
        else:
            raise UserHasNotPermissionError()

    def _request_cancel(self, task_id: str) -> None:
        if task_id in self.tasks:
            self._do_cancel_task(task_id)
        else:
            self.event_bus.push(
                Event(
                    type=EventType.TASK_CANCEL_REQUEST,
                    payload=task_id,
                    # Use `NONE` for internal events
                    permissions=PermissionInfo(public_mode=PublicMode.NONE),
                )
            )

    def _do_cancel_task(self, task_id: str) -> None:
        task = self.repo.get_or_raise(task_id)
        if task_id in self.tasks:
            cancelled = self.tasks[task_id].cancel()
            # Only updating status when the task is actually cancelled.
            if cancelled:
                logger.info(f"Successfully cancelled task {task_id}")
                task.status = TaskStatus.CANCELLED.value
                self.repo.save(task)
                for listener in self._listeners:
                    listener.on_task_cancel(task.id, task.get_type())
            else:
                logger.info(f"Failed to cancel task {task_id}")

    @override
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        if task := self.repo.get(task_id):
            return task.to_dto(with_logs)
        else:
            raise TaskNotFoundError(detail=f"Failed to retrieve task {task_id} in db")

    @override
    def list_tasks(self, task_filter: TaskListFilter) -> list[TaskDTO]:
        return [task.to_dto() for task in self._list_db_tasks(task_filter)]

    def _list_db_tasks(self, task_filter: TaskListFilter) -> list[TaskJob]:
        current_user = require_current_user()
        user = None if current_user.is_site_admin() else current_user.impersonator
        return self.repo.list(task_filter, user)

    @override
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        if task_id in self.tasks:
            try:
                logger.info(f"🤔 Awaiting task '{task_id}' {timeout_sec}s...")
                self.tasks[task_id].result(timeout_sec)
                logger.info(f"📌 Task '{task_id}' done.")
            except TimeoutError as timeout_exc:
                error_msg = f"Timeout while awaiting task '{task_id}'"
                logger.warning(error_msg)
                raise TimeoutError(error_msg) from timeout_exc
            except Exception as exc:
                logger.critical(f"🤕 Task '{task_id}' failed: {exc}.")
                raise
        else:
            logger.warning(f"Task '{task_id}' not handled by this worker, will poll for task completion from db")
            end = time.time() + timeout_sec
            while time.time() < end:
                with db():
                    task_status = db.session.execute(select(TaskJob.status).where(TaskJob.id == task_id)).scalar()
                    if task_status is None:
                        logger.error(f"Awaited task '{task_id}' was not found")
                        return
                    if TaskStatus(task_status).is_final():
                        return
                logger.info("💤 Sleeping 2 seconds...")
                time.sleep(2)
            error_msg = f"Timeout while awaiting task '{task_id}'"
            logger.warning(error_msg)
            raise TimeoutError(error_msg)

    def _run_task(
        self,
        callback: Task,
        task_id: str,
        task_type: TaskType,
        jwt_user: JWTUser,
        custom_event_messages: CustomTaskEventMessages | None = None,
    ) -> None:
        # We need to catch all exceptions so that the calling thread is guaranteed
        # to not die
        with task_context(task_id=task_id, user=jwt_user):
            try:
                status = TaskStatus.FAILED
                for listener in self._listeners:
                    listener.on_task_start(task_id, task_type)

                # attention: this function is executed in a thread, not in the main process
                with db():
                    # Important to keep this retry for now,
                    # in case commit is not visible (read from replica ...)
                    task = retry(lambda: self.repo.get_or_raise(task_id))
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
                    stmt = update(TaskJob).where(TaskJob.id == task_id).values(status=TaskStatus.RUNNING.value)
                    db.session.execute(stmt)
                    db.session.commit()
                logger.info(f"Task {task_id} set to RUNNING")

                with db():
                    # We must use the DB session attached to the current thread
                    result = callback(TaskLogAndProgressRecorder(task_id, db.session, self.event_bus))

                status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                logger.info(f"Task {task_id} ended with status {status}")

                with db():
                    # Do not use the `timezone.utc` timezone to preserve a naive datetime.
                    completion_date = current_time() if status.is_final() else None
                    stmt = (
                        update(TaskJob)
                        .where(TaskJob.id == task_id)
                        .values(
                            status=status.value,
                            result_msg=result.message,
                            result_status=result.success,
                            result=result.return_value,
                            completion_date=completion_date,
                        )
                    )
                    db.session.execute(stmt)
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
                        stmt = (
                            update(TaskJob)
                            .where(TaskJob.id == task_id)
                            .values(
                                status=TaskStatus.FAILED.value,
                                result_msg=str(exc),
                                result_status=False,
                                completion_date=current_time(),
                            )
                        )
                        db.session.execute(stmt)
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
            finally:
                for listener in self._listeners:
                    listener.on_task_end(task_id, task_type, status)

                # Task has been updated in database, we can safely remove it from running tasks
                if task_id in self.tasks:
                    del self.tasks[task_id]

    @override
    def get_task_progress(self, task_id: str) -> int | None:
        task = self.repo.get_or_raise(task_id)
        user = get_current_user()
        if user and (user.is_site_admin() or user.is_admin_token() or task.owner_id == user.impersonator):
            return task.progress
        else:
            raise UserHasNotPermissionError()

    @override
    def delete_task_by_creation_date(self, task_retention_duration: int) -> int:
        return self.repo.delete_by_creation_date(task_retention_duration=task_retention_duration)
