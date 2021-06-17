import subprocess
import threading
from pathlib import Path
from typing import Callable, Any
from uuid import UUID, uuid4

from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.common.utils.fastapi_sqlalchemy import db
from antarest.launcher.business.ilauncher import (
    ILauncher,
    LauncherInitException,
)
from antarest.launcher.model import JobStatus
from antarest.storage.service import StorageService


class StudyVersionNotSupported(Exception):
    pass


class LocalLauncher(ILauncher):
    def __init__(
        self, config: Config, storage_service: StorageService
    ) -> None:
        super().__init__(config, storage_service)

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:
        if self.config.launcher.local is None:
            raise LauncherInitException()

        antares_solver_path = self.config.launcher.local.binaries[version]
        if antares_solver_path is None:
            raise StudyVersionNotSupported()
        else:
            uuid = uuid4()
            study_path = self.storage_service.get_study_path(
                study_uuid, params
            )
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(self, antares_solver_path, study_path, uuid),
            )
            job.start()
            return uuid

    def _callback(self, process: Any, uuid: UUID, status: JobStatus) -> None:
        for callback in self.callbacks:
            callback(str(uuid), status, (not process.returncode == 0))

    def _compute(
        self, antares_solver_path: Path, study_path: Path, uuid: UUID
    ) -> None:
        process = subprocess.run(
            [antares_solver_path, study_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        with db():
            self._callback(
                process,
                uuid,
                JobStatus.FAILED
                if (not process.returncode == 0)
                else JobStatus.SUCCESS,
            )

    def add_statusupdate_callback(
        self, callback: Callable[[str, JobStatus, bool], None]
    ) -> None:
        self.callbacks.append(callback)
