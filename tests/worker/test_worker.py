from pathlib import Path
from typing import List
from unittest.mock import MagicMock

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.tasks.model import TaskResult
from antarest.eventbus.main import build_eventbus
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand
from tests.conftest import autoretry_assert


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
        ),
        task_queue,
    )

    assert not (tmp_path / "foo").exists()

    worker = DummyWorker(event_bus, [task_queue], tmp_path)
    worker.start(threaded=True)

    autoretry_assert(lambda: (tmp_path / "foo").exists(), 2)
