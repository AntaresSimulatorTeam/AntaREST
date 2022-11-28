import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import cast, IO

from pydantic import BaseModel

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import Config, LocalConfig
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.model import TaskResult
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand


logger = logging.getLogger(__name__)


GENERATE_TIMESERIES_TASK_NAME = "generate-timeseries"
GENERATE_KIRSHOFF_CONSTRAINTS_TASK_NAME = "generate-kirshoff-constraints"


class GenerateTimeseriesTaskArgs(BaseModel):
    study_id: str
    study_path: str
    managed: bool
    study_version: str


class SimulatorWorker(AbstractWorker):
    def __init__(
        self,
        event_bus: IEventBus,
        matrix_service: MatrixService,
        config: Config,
    ):
        super().__init__(
            "Simulator worker",
            event_bus,
            [
                GENERATE_TIMESERIES_TASK_NAME,
                GENERATE_KIRSHOFF_CONSTRAINTS_TASK_NAME,
            ],
        )
        self.config = config
        # this will raise an error if not properly configured
        self.binaries = (self.config.launcher.local or LocalConfig()).binaries
        self.study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=UriResolverService(matrix_service=matrix_service),
            cache=LocalCache(),
        )

    def execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        if task_info.task_type == GENERATE_TIMESERIES_TASK_NAME:
            return self.execute_timeseries_generation_task(task_info)
        elif task_info.task_type == GENERATE_KIRSHOFF_CONSTRAINTS_TASK_NAME:
            return self.execute_kirshoff_constraint_generation_task(task_info)
        raise NotImplementedError(
            f"{task_info.task_type} is not implemented by this worker"
        )

    def execute_kirshoff_constraint_generation_task(
        self, task_info: WorkerTaskCommand
    ) -> TaskResult:
        raise NotImplementedError

    def execute_timeseries_generation_task(
        self, task_info: WorkerTaskCommand
    ) -> TaskResult:
        result = TaskResult(success=True, message="", return_value="")
        task = GenerateTimeseriesTaskArgs.parse_obj(task_info.task_args)
        binary = (
            self.binaries[task.study_version]
            if task.study_version in self.binaries
            else list(self.binaries.values())[0]
        )
        file_study = self.study_factory.create_from_fs(
            Path(task.study_path), task.study_id, use_cache=False
        )
        if task.managed:
            with db():
                file_study.tree.denormalize()

        def append_output(line: str) -> None:
            result.return_value += line  # type: ignore

        try:
            end = False

            def stop_reading() -> bool:
                return end

            process = subprocess.Popen(
                [
                    binary,
                    "-i",
                    task.study_path,
                    "-g",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
            )
            thread = threading.Thread(
                target=lambda: LogTailManager.follow(
                    cast(IO[str], process.stdout),
                    append_output,
                    stop_reading,
                    None,
                ),
                daemon=True,
            )
            thread.start()

            while True:
                if process.poll() is not None:
                    break
                time.sleep(1)

            result.success = process.returncode == 0
        except Exception as e:
            logger.error(
                f"Failed to generate timeseries for study located at {task.study_path}",
                exc_info=e,
            )
            result.success = False
            result.message = repr(e)
        finally:
            if task.managed:
                with db():
                    file_study.tree.normalize()
            end = True
        return result
