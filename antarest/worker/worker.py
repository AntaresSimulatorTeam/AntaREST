import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Union, Any

from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.interfaces.service import IService
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.tasks.model import TaskResult
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MAX_WORKERS = 10


class WorkerTaskResult(BaseModel):
    task_id: str
    task_result: TaskResult


class WorkerTaskCommand(BaseModel):
    task_id: str
    task_type: str
    task_args: Dict[str, Union[int, float, bool, str]]


class _WorkerTaskEndedCallback:
    """
    Callback function which uses the event bus to notify
    that the worker task is completed (or cancelled).
    """

    def __init__(
        self,
        event_bus: IEventBus,
        task_id: str,
    ) -> None:
        self._event_bus = event_bus
        self._task_id = task_id

    # NOTE: it seems that mypy has an issue with `concurrent.futures.Future`,
    # for this reason we have annotated the `future` parameter with a string.
    def __call__(self, future: "Future[Any]") -> None:
        result = future.result()
        event = Event(
            type=EventType.WORKER_TASK_ENDED,
            payload=WorkerTaskResult(
                task_id=self._task_id, task_result=result
            ),
            # Use `NONE` for internal events
            permissions=PermissionInfo(public_mode=PublicMode.NONE),
        )
        self._event_bus.push(event)


# fixme: `AbstractWorker` should not inherit from `IService`
class AbstractWorker(IService):
    def __init__(
        self,
        name: str,
        event_bus: IEventBus,
        accept: List[str],
    ) -> None:
        super().__init__()
        # fixme: `AbstractWorker` should not have any `thread` attribute
        del self.thread
        self.name = name
        self.event_bus = event_bus
        self.accept = accept
        self.threadpool = ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
            thread_name_prefix="worker_task_",
        )
        self.lock = threading.Lock()

    # fixme: `AbstractWorker.start` should not have any `threaded` parameter
    def start(self, threaded: bool = True) -> None:
        for task_type in self.accept:
            self.event_bus.add_queue_consumer(
                self._listen_for_tasks, task_type
            )
        # Wait a short time to allow the event bus to have the opportunity
        # to process the tasks as soon as possible
        time.sleep(0.01)

    # fixme: `AbstractWorker` should not have any `_loop` function
    def _loop(self) -> None:
        pass

    async def _listen_for_tasks(self, event: Event) -> None:
        logger.info(f"Accepting new task {event.json()}")
        task_info = WorkerTaskCommand.parse_obj(event.payload)
        self.event_bus.push(
            Event(
                type=EventType.WORKER_TASK_STARTED,
                payload=task_info,
                # Use `NONE` for internal events
                permissions=PermissionInfo(public_mode=PublicMode.NONE),
            )
        )
        with self.lock:
            # fmt: off
            future = self.threadpool.submit(self._safe_execute_task, task_info)
            callback = _WorkerTaskEndedCallback(self.event_bus, task_info.task_id)
            future.add_done_callback(callback)
            # fmt: on

    def _safe_execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        try:
            return self.execute_task(task_info)
        except Exception as e:
            logger.error(
                f"Unexpected error occurred when executing task {task_info.json()}",
                exc_info=e,
            )
            return TaskResult(success=False, message=repr(e))

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        raise NotImplementedError()
