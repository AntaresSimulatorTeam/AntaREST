import asyncio
import datetime
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from http import HTTPStatus
from typing import Callable, Optional, List, Dict, Awaitable

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
    EventChannelDirectory,
)
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo
from antarest.core.requests import (
    RequestParameters,
    MustBeAuthenticatedError,
    UserHasNotPermissionError,
)
from antarest.core.tasks.model import (
    TaskDTO,
    TaskListFilter,
    TaskJob,
    TaskStatus,
    TaskJobLog,
    TaskResult,
    CustomTaskEventMessages,
    TaskEventPayload,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import retry

logger = logging.getLogger(__name__)

TaskUpdateNotifier = Callable[[str], None]
Task = Callable[[TaskUpdateNotifier], TaskResult]


class ITaskService(ABC):
    @abstractmethod
    def add_task(
        self,
        action: Task,
        name: Optional[str],
        custom_event_messages: Optional[CustomTaskEventMessages],
        request_params: RequestParameters,
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    def status_task(
        self,
        task_id: str,
        request_params: RequestParameters,
        with_logs: bool = False,
    ) -> TaskDTO:
        raise NotImplementedError()

    @abstractmethod
    def list_tasks(
        self, task_filter: TaskListFilter, request_params: RequestParameters
    ) -> List[TaskDTO]:
        raise NotImplementedError()

    @abstractmethod
    def await_task(
        self, task_id: str, timeout_sec: Optional[int] = None
    ) -> None:
        raise NotImplementedError()


def noop_notifier(message: str) -> None:
    pass


DEFAULT_AWAIT_MAX_TIMEOUT = 172800


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
        self.threadpool = ThreadPoolExecutor(
            max_workers=config.tasks.max_workers, thread_name_prefix="taskjob_"
        )
        self.event_bus.add_listener(self.create_task_event_callback())
        # set the status of previously running job to FAILED due to server restart
        self._fix_running_status()

    def add_task(
        self,
        action: Task,
        name: Optional[str],
        custom_event_messages: Optional[CustomTaskEventMessages],
        request_params: RequestParameters,
    ) -> str:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        task = self.repo.save(
            TaskJob(
                name=name or "Unnamed",
                owner_id=request_params.user.impersonator,
            )
        )

        self.event_bus.push(
            Event(
                type=EventType.TASK_ADDED,
                payload=TaskEventPayload(
                    id=task.id, message=custom_event_messages.start
                ).dict()
                if custom_event_messages is not None
                else f"Task {task.id} added",
                permissions=PermissionInfo(
                    owner=request_params.user.impersonator
                ),
            )
        )
        future = self.threadpool.submit(
            self._run_task, action, task.id, custom_event_messages
        )
        self.tasks[task.id] = future
        return str(task.id)

    def create_task_event_callback(self) -> Callable[[Event], Awaitable[None]]:
        async def task_event_callback(event: Event) -> None:
            if event.type == EventType.TASK_CANCEL_REQUEST:
                self._cancel_task(str(event.payload), dispatch=False)

        return task_event_callback

    def cancel_task(
        self, task_id: str, params: RequestParameters, dispatch: bool = False
    ) -> None:
        task = self.repo.get_or_raise(task_id)
        if params.user and (
            params.user.is_site_admin()
            or task.owner_id == params.user.impersonator
        ):
            self._cancel_task(task_id, dispatch)
        else:
            raise UserHasNotPermissionError()

    def _cancel_task(self, task_id: str, dispatch: bool = False) -> None:
        task = self.repo.get_or_raise(task_id)
        if task_id in self.tasks:
            self.tasks[task_id].cancel()
            task.status = TaskStatus.CANCELLED
            self.repo.save(task)
        elif dispatch:
            self.event_bus.push(
                Event(type=EventType.TASK_CANCEL_REQUEST, payload=task_id)
            )

    def status_task(
        self,
        task_id: str,
        request_params: RequestParameters,
        with_logs: bool = False,
    ) -> TaskDTO:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        task = self.repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Failed to retrieve task {task_id} in db",
            )
        return task.to_dto(with_logs)

    def list_tasks(
        self, task_filter: TaskListFilter, request_params: RequestParameters
    ) -> List[TaskDTO]:
        return [
            task.to_dto()
            for task in self.list_db_tasks(task_filter, request_params)
        ]

    def list_db_tasks(
        self, task_filter: TaskListFilter, request_params: RequestParameters
    ) -> List[TaskJob]:
        if not request_params.user:
            raise MustBeAuthenticatedError()
        return self.repo.list(
            task_filter,
            request_params.user.impersonator
            if not request_params.user.is_site_admin()
            else None,
        )

    def await_task(
        self, task_id: str, timeout_sec: Optional[int] = None
    ) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].result(
                timeout_sec or DEFAULT_AWAIT_MAX_TIMEOUT
            )
        else:
            logger.warning(
                f"Task {task_id} not handled by this worker, will poll for task completion from db"
            )
            end = time.time() + (timeout_sec or DEFAULT_AWAIT_MAX_TIMEOUT)
            while time.time() < end:
                task = self.repo.get(task_id)
                if not task:
                    logger.error(f"Awaited task {task_id} was not found")
                    break
                if TaskStatus(task.status).is_final():
                    break
                time.sleep(2)

    def _run_task(
        self,
        callback: Task,
        task_id: str,
        custom_event_messages: Optional[CustomTaskEventMessages] = None,
    ) -> None:

        self.event_bus.push(
            Event(
                type=EventType.TASK_RUNNING,
                payload=TaskEventPayload(
                    id=task_id, message=custom_event_messages.running
                ).dict()
                if custom_event_messages is not None
                else f"Task {task_id} is running",
                channel=EventChannelDirectory.TASK + task_id,
            )
        )

        with db():
            task = retry(lambda: self.repo.get_or_raise(task_id))
            task.status = TaskStatus.RUNNING.value
            self.repo.save(task)
            try:
                result = callback(self._task_logger(task_id))
                self._update_task_status(
                    task_id,
                    TaskStatus.COMPLETED
                    if result.success
                    else TaskStatus.FAILED,
                    result.success,
                    result.message,
                    result.return_value,
                )
                self.event_bus.push(
                    Event(
                        type=EventType.TASK_COMPLETED
                        if result.success
                        else EventType.TASK_FAILED,
                        payload=TaskEventPayload(
                            id=task_id, message=custom_event_messages.end
                        ).dict()
                        if custom_event_messages is not None
                        else f'Task {task_id} {"completed" if result.success else "failed"}',
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )
            except Exception as e:
                logger.error(
                    f"Exception when running task {task_id}", exc_info=e
                )
                self._update_task_status(
                    task_id, TaskStatus.FAILED, False, str(e)
                )
                self.event_bus.push(
                    Event(
                        type=EventType.TASK_FAILED,
                        payload=TaskEventPayload(
                            id=task_id, message=custom_event_messages.end
                        ).dict()
                        if custom_event_messages is not None
                        else f"Task {task_id} failed",
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )

    def _task_logger(self, task_id: str) -> Callable[[str], None]:
        def log_msg(message: str) -> None:
            task = self.repo.get(task_id)
            if task:
                task.logs.append(TaskJobLog(message=message, task_id=task_id))
                self.repo.save(task)

        return log_msg

    def _fix_running_status(self) -> None:
        with db():
            previous_tasks = self.list_db_tasks(
                TaskListFilter(
                    status=[TaskStatus.RUNNING, TaskStatus.PENDING]
                ),
                request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
            )
            for task in previous_tasks:
                self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    False,
                    "Task was interrupted due to server restart",
                )

    def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: bool,
        message: str,
        command_result: Optional[str] = None,
    ) -> None:
        task = self.repo.get_or_raise(task_id)
        task.status = status.value
        task.result_msg = message
        task.result_status = result
        task.result = command_result
        if status.is_final():
            task.completion_date = datetime.datetime.utcnow()
        self.repo.save(task)
