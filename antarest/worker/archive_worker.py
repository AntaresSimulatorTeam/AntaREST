import logging
from pathlib import Path

from pydantic import BaseModel

from antarest.core.config import Config
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

    def __init__(
        self,
        event_bus: IEventBus,
        workspace: str,
        local_root: Path,
        config: Config,
    ):
        self.workspace = workspace
        self.config = config
        self.local_root = local_root
        super().__init__(
            "Unarchive worker",
            event_bus,
            [f"{ArchiveWorker.TASK_TYPE}_{workspace}"],
        )

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        logger.info(f"Executing task {task_info.json()}")
        try:
            archive_args = ArchiveTaskArgs.parse_obj(task_info.task_args)
            dest = self.translate_path(Path(archive_args.dest))
            src = self.translate_path(Path(archive_args.src))
            logger.info(f"Extracting {src} into {dest}")
            unzip(
                dest,
                src,
                remove_source_zip=archive_args.remove_src,
            )
            logger.info(f"Successfuly extracted task {src} into {dest}")
            return TaskResult(success=True, message="")
        except Exception as e:
            logger.warning(
                f"Failed to unarchive {archive_args.src} into {archive_args.dest}",
                exc_info=e,
            )
            return TaskResult(success=False, message=str(e))

    def translate_path(self, path: Path) -> Path:
        workspace = self.config.storage.workspaces[self.workspace]
        return self.local_root / path.relative_to(workspace.path)
