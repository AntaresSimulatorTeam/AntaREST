from typing import Callable, Optional, List

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskResult, TaskDTO, TaskListFilter

TaskUpdateNotifier = Callable[[str], None]
Task = Callable[[TaskUpdateNotifier], TaskResult]


class TaskJobService:
    def __init__(self, config: Config, event_bus: IEventBus):
        self.config = config
        self.event_bus = event_bus

    def add_task(
        self,
        action: Task,
        name: Optional[str],
        request_params: RequestParameters,
    ) -> str:
        pass

    def status_task(
        self, task_id: str, request_params: RequestParameters
    ) -> TaskDTO:
        pass

    def list_tasks(
        self, task_filter: TaskListFilter, request_params: RequestParameters
    ) -> List[TaskDTO]:
        pass

    def stop_task(
        self, task_id: str, request_params: RequestParameters
    ) -> None:
        pass
