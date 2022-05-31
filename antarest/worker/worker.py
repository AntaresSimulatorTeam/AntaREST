import abc
import subprocess
import time
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
    task_id: str
    task_type: str
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
        self.futures: Dict[str, Future[TaskResult]] = {}

    def start(self, threaded: bool = False) -> None:
        if threaded:
            self.task_watcher.start()
        else:
            self._loop()

    async def listen_for_tasks(self, event: Event) -> None:
        task_info = WorkerTaskCommand.parse_obj(event.payload)
        self.event_bus.push(
            Event(type=EventType.WORKER_TASK_STARTED, payload=task_info)
        )
        self.futures[task_info.task_id] = self.threadpool.submit(
            self.execute_task, task_info
        )

    @abstractmethod
    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        raise NotImplementedError()

    def _loop(self) -> None:
        while True:
            for task_id, future in self.futures.items():
                if future.done():
                    self.event_bus.push(
                        Event(
                            type=EventType.WORKER_TASK_ENDED,
                            payload=WorkerTaskResult(
                                task_id=task_id, task_result=future.result()
                            ),
                        )
                    )
            time.sleep(2)
