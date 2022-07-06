import subprocess
from typing import cast

from antarest.core.tasks.model import TaskResult
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand


class ArchiveWorker(AbstractWorker):
    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        raise NotImplementedError
