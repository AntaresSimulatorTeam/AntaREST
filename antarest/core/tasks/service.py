import asyncio
import datetime
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
from http import HTTPStatus
from typing import Callable, Optional, List, Dict, Awaitable, Union, cast

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
    TaskType,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import retry
from antarest.worker.worker import WorkerTaskCommand, WorkerTaskResult

logger = logging.getLogger(__name__)

TaskUpdateNotifier = Callable[[str], None]
Task = Callable[[TaskUpdateNotifier], TaskResult]


class ITaskService(ABC):
    @abstractmethod
    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: Dict[str, Union[int, float, bool, str]],
        name: Optional[str],
        ref_id: Optional[str],
        request_params: RequestParameters,
    ) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def add_task(
        self,
        action: Task,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
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
        self.event_bus.add_listener(
            self.create_task_event_callback(), [EventType.TASK_CANCEL_REQUEST]
        )
        self.remote_workers = config.tasks.remote_workers
        # set the status of previously running job to FAILED due to server restart
        self._fix_running_status()

    def _create_worker_task(
        self,
        task_id: str,
        task_type: str,
        task_args: Dict[str, Union[int, float, bool, str]],
    ) -> Callable[[TaskUpdateNotifier], TaskResult]:
        task_result_wrapper: List[TaskResult] = []

        def _create_awaiter(
            res_wrapper: List[TaskResult],
        ) -> Callable[[Event], Awaitable[None]]:
            async def _await_task_end(event: Event) -> None:
                task_event = WorkerTaskResult.parse_obj(event.payload)
                if task_event.task_id == task_id:
                    res_wrapper.append(task_event.task_result)

            return _await_task_end

        def _send_worker_task(logger: TaskUpdateNotifier) -> TaskResult:
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
                ),
                task_type,
            )
            while not task_result_wrapper:
                time.sleep(1)
            self.event_bus.remove_listener(listener_id)
            return task_result_wrapper[0]

        return _send_worker_task

    def check_remote_worker_for_queue(self, task_queue: str) -> bool:
        for rw in self.remote_workers:
            if task_queue in rw.queues:
                return True
        return False

    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: Dict[str, Union[int, float, bool, str]],
        name: Optional[str],
        ref_id: Optional[str],
        request_params: RequestParameters,
    ) -> Optional[str]:
        if not self.check_remote_worker_for_queue(task_queue):
            logger.warning(
                f"Failed to find configured remote worker for task queue {task_queue}"
            )
            return None

        task = self._create_task(name, task_type, ref_id, request_params)
        self._launch_task(
            self._create_worker_task(str(task.id), task_queue, task_args),
            task,
            None,
            request_params,
        )
        return str(task.id)

    def add_task(
        self,
        action: Task,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        custom_event_messages: Optional[CustomTaskEventMessages],
        request_params: RequestParameters,
    ) -> str:
        task = self._create_task(name, task_type, ref_id, request_params)
        self._launch_task(action, task, custom_event_messages, request_params)
        return str(task.id)

    def _create_task(
        self,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        request_params: RequestParameters,
    ) -> TaskJob:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        return self.repo.save(
            TaskJob(
                name=name or "Unnamed",
                owner_id=request_params.user.impersonator,
                type=task_type,
                ref_id=ref_id,
            )
        )

    def _launch_task(
        self,
        action: Task,
        task: TaskJob,
        custom_event_messages: Optional[CustomTaskEventMessages],
        request_params: RequestParameters,
    ) -> None:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        self.event_bus.push(
            Event(
                type=EventType.TASK_ADDED,
                payload=TaskEventPayload(
                    id=task.id,
                    message=custom_event_messages.start
                    if custom_event_messages is not None
                    else f"Task {task.id} added",
                ).dict(),
                permissions=PermissionInfo(
                    owner=request_params.user.impersonator
                ),
            )
        )
        future = self.threadpool.submit(
            self._run_task, action, task.id, custom_event_messages
        )
        self.tasks[task.id] = future

    def create_task_event_callback(self) -> Callable[[Event], Awaitable[None]]:
        async def task_event_callback(event: Event) -> None:
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
            task.status = TaskStatus.CANCELLED.value
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
        logger.info(f"Awaiting task {task_id}")
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
                with db():
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
                    id=task_id,
                    message=custom_event_messages.running
                    if custom_event_messages is not None
                    else f"Task {task_id} is running",
                ).dict(),
                channel=EventChannelDirectory.TASK + task_id,
            )
        )

        logger.info(f"Starting task {task_id}")
        with db():
            task = retry(lambda: self.repo.get_or_raise(task_id))
            task.status = TaskStatus.RUNNING.value
            self.repo.save(task)
            logger.info(f"Task {task_id} set to RUNNING")
        try:
            with db():
                result = callback(self._task_logger(task_id))
            logger.info(f"Task {task_id} ended")
            with db():
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
                        id=task_id,
                        message=custom_event_messages.end
                        if custom_event_messages is not None
                        else f'Task {task_id} {"completed" if result.success else "failed"}',
                    ).dict(),
                    channel=EventChannelDirectory.TASK + task_id,
                )
            )
        except Exception as e:
            logger.error(f"Exception when running task {task_id}", exc_info=e)
            with db():
                self._update_task_status(
                    task_id, TaskStatus.FAILED, False, repr(e)
                )
            self.event_bus.push(
                Event(
                    type=EventType.TASK_FAILED,
                    payload=TaskEventPayload(
                        id=task_id,
                        message=custom_event_messages.end
                        if custom_event_messages is not None
                        else f"Task {task_id} failed",
                    ).dict(),
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
