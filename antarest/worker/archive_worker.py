import logging
from pathlib import Path

from pydantic import BaseModel

from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.model import TaskResult
from antarest.core.utils.utils import unzip
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand


logger = logging.getLogger(__name__)


class ArchiveTaskArgs(BaseModel):
    src: str
    dest: str
    remove_src: bool = False


class ArchiveWorker(AbstractWorker):
    TASK_TYPE = "unarchive"

    def __init__(self, event_bus: IEventBus, workspace: str):
        super().__init__(
            "Unarchive worker",
            event_bus,
            [f"{ArchiveWorker.TASK_TYPE}_{workspace}"],
        )

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        logger.info(f"Executing task {task_info.json()}")
        archive_args = ArchiveTaskArgs.parse_obj(task_info.task_args)
        try:
            unzip(
                Path(archive_args.dest),
                Path(archive_args.src),
                remove_source_zip=archive_args.remove_src,
            )
            return TaskResult(success=True, message="")
        except Exception as e:
            logger.warning(
                f"Failed to unarchive {archive_args.src} into {archive_args.dest}",
                exc_info=e,
            )
            return TaskResult(success=False, message=str(e))
