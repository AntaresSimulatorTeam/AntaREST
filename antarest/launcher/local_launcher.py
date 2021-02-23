import subprocess
import threading
from pathlib import Path
from threading import Thread
from typing import Dict, Optional, Callable, List, Any
from uuid import UUID, uuid4

from antarest.common.config import Config
from antarest.launcher.ilauncher import ILauncher
from antarest.launcher.model import JobResult, JobStatus


class StudyVersionNotSupported(Exception):
    pass


class LocalLauncher(ILauncher):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.callbacks: List[Callable[[JobResult], None]] = []

    def run_study(self, study_path: Path, version: str) -> UUID:
        antares_solver_path = self.config[f"launcher.local.binaries.{version}"]
        if antares_solver_path is None:
            raise StudyVersionNotSupported()
        else:
            uuid = uuid4()
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(self, antares_solver_path, study_path, uuid),
            )
            job.start()
            return uuid

    def _callback(self, process: Any, uuid: UUID) -> None:
        if process.returncode == 0:
            execution_status = JobStatus.SUCCESS
        else:
            execution_status = JobStatus.FAILED

        result = JobResult(
            id=str(uuid),
            job_status=execution_status,
            msg=process.stdout.decode("latin-1").rstrip(),
            exit_code=process.returncode,
        )
        for callback in self.callbacks:
            callback(result)

    def _compute(
        self, antares_solver_path: Path, study_path: Path, uuid: UUID
    ) -> None:
        process = subprocess.run(
            [antares_solver_path, study_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        self._callback(process, uuid)

    def add_callback(self, callback: Callable[[JobResult], None]) -> None:
        self.callbacks.append(callback)
