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
from tests.conftest import auto_retry_assert


class DummyWorker(AbstractWorker):
    def __init__(
        self, event_bus: IEventBus, accept: List[str], tmp_path: Path
    ):
        super().__init__("test", event_bus, accept)
        self.tmp_path = tmp_path

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        relative_path = task_info.task_args["file"]
        (self.tmp_path / relative_path).touch()
        return TaskResult(success=True, message="")


def test_simple_task(tmp_path: Path):
    task_queue = "do_stuff"
    event_bus = build_eventbus(MagicMock(), Config(), autostart=True)
    event_bus.queue(
        Event(
            type=EventType.WORKER_TASK,
            payload=WorkerTaskCommand(
                task_type="touch stuff",
                task_id="some task",
                task_args={"file": "foo"},
            ),
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        ),
        task_queue,
    )

    msg = []

    async def notify_started(event: Event):
        msg.append("started")

    async def notify_ended(event: Event):
        msg.append("ended")

    event_bus.add_listener(notify_started, [EventType.WORKER_TASK_STARTED])
    event_bus.add_listener(notify_ended, [EventType.WORKER_TASK_ENDED])

    assert not (tmp_path / "foo").exists()

    worker = DummyWorker(event_bus, [task_queue], tmp_path)
    worker.start(threaded=True)

    auto_retry_assert(lambda: (tmp_path / "foo").exists(), timeout=60)

    # IMPORTANT: the worker loop has a duration of 2 seconds,
    # so we need to wait at least this duration to get the end event notification.
    time.sleep(2.1)
    assert msg == ["started", "ended"]
