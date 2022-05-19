import abc
import subprocess
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread
from typing import List, Dict, Union, cast

from pydantic import BaseModel

from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.tasks.model import TaskResult

MAX_WORKERS = 10


class WorkerTaskResult(BaseModel):
    task_id: str
    task_result: TaskResult


class WorkerTaskCommand(BaseModel):
    task_type: str
    task_name: str
    task_args: Dict[str, Union[int, float, bool, str]]


class AbstractWorker(abc.ABC):
    def __init__(self, event_bus: IEventBus, accept: List[str]) -> None:
        self.event_bus = event_bus
        for task_type in accept:
            self.event_bus.add_queue_consumer(self.listen_for_tasks, task_type)
        self.threadpool = ThreadPoolExecutor(
            max_workers=MAX_WORKERS, thread_name_prefix="workertask_"
        )
        self.task_watcher = Thread(target=self._loop, daemon=True)
        self.futures: List[Future[TaskResult]] = []

    async def listen_for_tasks(self, event: Event) -> None:
        task_info = cast(WorkerTaskCommand, event.payload)
        self.futures.append(
            self.threadpool.submit(self.execute_task, task_info)
        )

    @abstractmethod
    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        raise NotImplementedError()

    def _loop(self) -> None:
        while True:
            for future in self.futures:
                if future.done():
                    self.event_bus.push(
                        Event(
                            type=EventType.WORKER_TASK_ENDED,
                            payload=future.result(),
                        )
                    )


class WindowsWorker(AbstractWorker):
    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        self.event_bus.push(Event(type=EventType.WORKER_TASK_STARTED))
        proc = subprocess.Popen(
            ["unzip", cast(str, task_info.task_args["file"])]
        )
        proc.wait()
        return TaskResult(success=True, message="")
