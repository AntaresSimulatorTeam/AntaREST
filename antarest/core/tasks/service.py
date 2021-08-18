import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from http import HTTPStatus
from typing import Callable, Optional, List, Dict

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
    MustBeAuthenticatedError,
)
from antarest.core.tasks.model import (
    TaskResult,
    TaskDTO,
    TaskListFilter,
    TaskJob,
    TaskStatus,
    TaskJobLog,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.utils.fastapi_sqlalchemy import db

logger = logging.getLogger(__name__)


TaskUpdateNotifier = Callable[[str], None]
Task = Callable[[TaskUpdateNotifier], TaskResult]


class TaskJobService:
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
        # set the status of previously running job to FAILED due to server restart
        self._fix_running_status()

    def add_task(
        self,
        action: Task,
        name: Optional[str],
        request_params: RequestParameters,
    ) -> str:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        task = self.repo.save(
            TaskJob(
                name=name or "Unnamed",
                owner_id=request_params.user.id,
            )
        )
        future = self.threadpool.submit(self._run_task, action, task)
        self.tasks[task.id] = future
        return str(task.id)

    def status_task(
        self, task_id: str, request_params: RequestParameters
    ) -> TaskDTO:
        if not request_params.user:
            raise MustBeAuthenticatedError()

        task = self.repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Failed to retrieve task {task_id} in db",
            )
        return task.to_dto()

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
            request_params.user.id
            if not request_params.user.is_site_admin()
            else None,
        )

    def await_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].result()

    def _run_task(self, callback: Task, task: TaskJob) -> None:
        with db():
            task.status = TaskStatus.RUNNING.value
            self.repo.save(task)
        try:
            result = callback(self._task_logger(task.id))
            self._update_task_status(
                task,
                TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                result.success,
                result.message,
            )
        except Exception as e:
            logger.error(
                f"Exception when running task {task.name}", exc_info=e
            )
            self._update_task_status(task, TaskStatus.FAILED, False, str(e))

    def _task_logger(self, task_id: str) -> Callable[[str], None]:
        def log_msg(message: str) -> None:
            task = self.repo.get(task_id)
            if task:
                task.logs.append(TaskJobLog(message=message, task_id=task_id))
                with db():
                    self.repo.save(task)

        return log_msg

    def _fix_running_status(self) -> None:
        previous_tasks = self.list_db_tasks(
            TaskListFilter(status=[TaskStatus.RUNNING, TaskStatus.PENDING]),
            request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        for task in previous_tasks:
            self._update_task_status(
                task,
                TaskStatus.FAILED,
                False,
                "Task was interrupted due to server restart",
            )

    def _update_task_status(
        self, task: TaskJob, status: TaskStatus, result: bool, message: str
    ) -> None:
        with db():
            task.status = status.value
            task.result_msg = message
            task.result_status = result
            if status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
                TaskStatus.TIMEOUT,
            ]:
                task.completion_date = datetime.datetime.utcnow()
            self.repo.save(task)
