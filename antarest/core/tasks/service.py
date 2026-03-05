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
from concurrent.futures import Future, ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Awaitable, Callable, Dict, List, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType, IEventBus
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.tasks.action import TaskActionDescriptor
from antarest.core.tasks.model import (
    CustomTaskEventMessages,
    TaskDTO,
    TaskEventPayload,
    TaskJob,
    TaskJobLog,
    TaskListFilter,
    TaskStatus,
    TaskType,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import get_current_user, require_current_user

if TYPE_CHECKING:
    from antarest.service_creator import CoreServices

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


class ITaskService(ABC):
    @abstractmethod
    def add_task(
        self,
        action: TaskActionDescriptor,
        name: Optional[str],
        task_type: TaskType,
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
        """
        Retrieves information about a task.

        Raise:
            TaskNotFoundError: if the task is not found in the database.
        """
        raise NotImplementedError()

    @abstractmethod
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
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
        self.config = config
        self.repo = repository
        self.event_bus = event_bus
        self.tasks: Dict[str, Future[None]] = {}
        self.threadpool = ThreadPoolExecutor(max_workers=config.tasks.max_workers, thread_name_prefix="taskjob_")
        self.event_bus.add_listener(self.create_task_event_callback(), [EventType.TASK_CANCEL_REQUEST])
        self._listeners = list(listeners) if listeners else []
        self._core_services: Optional["CoreServices"] = None

    def set_core_services(self, core_services: "CoreServices") -> None:
        """Set core services reference after construction (two-phase init)."""
        self._core_services = core_services

    @property
    def core_services(self) -> "CoreServices":
        if self._core_services is None:
            raise RuntimeError("CoreServices not set on TaskJobService. Call set_core_services() first.")
        return self._core_services

    @override
    def add_task(
        self,
        action: TaskActionDescriptor,
        name: Optional[str],
        task_type: TaskType,
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
        action: TaskActionDescriptor,
        task: TaskJob,
        custom_event_messages: Optional[CustomTaskEventMessages],
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
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        return [task.to_dto() for task in self._list_db_tasks(task_filter)]

    def _list_db_tasks(self, task_filter: TaskListFilter) -> List[TaskJob]:
        current_user = require_current_user()
        user = None if current_user.is_site_admin() else current_user.impersonator
        return self.repo.list(task_filter, user)

    @override
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        if task_id in self.tasks:
            try:
                logger.info(f"Awaiting task '{task_id}' {timeout_sec}s...")
                self.tasks[task_id].result(timeout_sec)
                logger.info(f"Task '{task_id}' done.")
            except TimeoutError as timeout_exc:
                error_msg = f"Timeout while awaiting task '{task_id}'"
                logger.warning(error_msg)
                raise TimeoutError(error_msg) from timeout_exc
            except Exception as exc:
                logger.critical(f"Task '{task_id}' failed: {exc}.")
                raise
        else:
            logger.warning(f"Task '{task_id}' not handled by this worker, will poll for task completion from db")
            end = time.time() + timeout_sec
            while time.time() < end:
                task_status = db.session.execute(select(TaskJob.status).where(TaskJob.id == task_id)).scalar()
                if task_status is None:
                    logger.error(f"Awaited task '{task_id}' was not found")
                    return
                if TaskStatus(task_status).is_final():
                    return
                logger.info("Sleeping 2 seconds...")
                time.sleep(2)
            error_msg = f"Timeout while awaiting task '{task_id}'"
            logger.warning(error_msg)
            raise TimeoutError(error_msg)

    def _run_task(
        self,
        action: TaskActionDescriptor,
        task_id: str,
        task_type: TaskType,
        jwt_user: JWTUser,
        custom_event_messages: Optional[CustomTaskEventMessages] = None,
    ) -> None:
        from antarest.core.tasks.execution import execute_task

        try:
            execute_task(
                task_id=task_id,
                task_type=task_type,
                action=action,
                core_services=self.core_services,
                event_bus=self.event_bus,
                repo=self.repo,
                jwt_user=jwt_user,
                custom_event_messages=custom_event_messages,
                listeners=self._listeners,
            )
        finally:
            # Task has been updated in database, we can safely remove it from running tasks
            if task_id in self.tasks:
                del self.tasks[task_id]

    def get_task_progress(self, task_id: str) -> Optional[int]:
        task = self.repo.get_or_raise(task_id)
        user = get_current_user()
        if user and (user.is_site_admin() or user.is_admin_token() or task.owner_id == user.impersonator):
            return task.progress
        else:
            raise UserHasNotPermissionError()

    @override
    def delete_task_by_creation_date(self, task_retention_duration: int) -> int:
        return self.repo.delete_by_creation_date(task_retention_duration=task_retention_duration)
