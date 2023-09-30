import time
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.tasks.model import TaskResult
from antarest.eventbus.main import build_eventbus
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand
from tests.helpers import auto_retry_assert


class DummyWorker(AbstractWorker):
    def __init__(self, event_bus: IEventBus, accept: List[str], tmp_path: Path):
        super().__init__("test", event_bus, accept)
        self.tmp_path = tmp_path

    def _execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        # simulate a "long" task ;-)
        time.sleep(0.01)
        relative_path = task_info.task_args["file"]
        (self.tmp_path / relative_path).touch()
        return TaskResult(success=True, message="")


def test_simple_task(tmp_path: Path):
    task_queue = "do_stuff"
    event_bus = build_eventbus(MagicMock(), Config(), autostart=True)
    command_event = Event(
        type=EventType.WORKER_TASK,
        payload=WorkerTaskCommand(
            task_type="touch stuff",
            task_id="some task",
            task_args={"file": "foo"},
        ),
        permissions=PermissionInfo(public_mode=PublicMode.READ),
    )
    event_bus.queue(command_event, task_queue)

    # Add some listeners to debug the event bus notifications
    msg = []

    async def notify(event: Event):
        msg.append(event.type.value)

    event_bus.add_listener(notify, [EventType.WORKER_TASK_STARTED])
    event_bus.add_listener(notify, [EventType.WORKER_TASK_ENDED])

    # Initialize and start a worker
    worker = DummyWorker(event_bus, [task_queue], tmp_path)
    worker.start()

    # Wait for the end of the processing
    # Set a big value to `timeout` if you want to debug the worker
    auto_retry_assert(lambda: (tmp_path / "foo").exists(), timeout=60)
    auto_retry_assert(
        lambda: msg == ["WORKER_TASK_STARTED", "WORKER_TASK_ENDED"],
        timeout=1,
        delay=0.1,
    )

    msg.clear()
    # Send a second event to check worker is still processing events
    event_bus.queue(command_event, task_queue)
    auto_retry_assert(
        lambda: msg == ["WORKER_TASK_STARTED", "WORKER_TASK_ENDED"],
        timeout=1,
        delay=0.1,
    )
