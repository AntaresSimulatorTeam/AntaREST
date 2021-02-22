import subprocess
import threading
from pathlib import Path
from threading import Thread
from typing import Dict
from uuid import UUID, uuid4

from antarest.common.config import Config
from antarest.launcher.ilauncher import ILauncher
from antarest.launcher.model import JobResult, JobStatus


class StudyVersionNotSupported(Exception):
    pass


class JobNotFound(Exception):
    pass


class LocalLauncher(ILauncher):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.jobs: Dict[UUID, Thread] = {}
        self.results: Dict[UUID, JobResult] = {}

    def run_study(self, study_path: Path, version: str) -> UUID:
        antares_solver_path = self.config[f"launcher.binaries.{version}"]
        if antares_solver_path is None:
            raise StudyVersionNotSupported()
        else:
            uuid = uuid4()
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(self, antares_solver_path, study_path, uuid),
            )
            self.jobs[uuid] = job
            job.start()
            return uuid

    def _compute(
        self, antares_solver_path: Path, study_path: Path, uuid: UUID
    ) -> None:
        process = subprocess.run(
            [antares_solver_path, study_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if process.returncode == 0:
            execution_status = JobStatus.SUCCESS
        else:
            execution_status = JobStatus.FAILED

        self.results[uuid] = JobResult(
            execution_status,
            msg=process.stdout.decode("latin-1").rstrip(),
            exit_code=process.returncode,
        )

    def get_result(self, uuid: UUID) -> JobResult:
        result = self.results.get(uuid, None)
        if result:
            return result

        job = self.jobs.get(uuid, None)
        if job is None:
            raise JobNotFound()
        return JobResult(JobStatus.RUNNING, "", 0)
