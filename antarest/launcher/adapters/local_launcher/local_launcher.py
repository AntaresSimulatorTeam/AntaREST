import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

from antarest.core.config import Config
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.model import JobStatus, LogType
from antarest.study.service import StudyService


class StudyVersionNotSupported(Exception):
    pass


class LocalLauncher(AbstractLauncher):
    def __init__(
        self,
        config: Config,
        storage_service: StudyService,
        callbacks: LauncherCallbacks,
    ) -> None:
        super().__init__(config, storage_service, callbacks)
        self.job_id_to_study_id: Dict[str, str] = {}

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
            self.job_id_to_study_id[str(uuid)] = study_uuid
            study_path = self.storage_service.get_study_path(
                study_uuid, params
            )
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(self, antares_solver_path, study_path, uuid),
            )
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
        del self.job_id_to_study_id[str(uuid)]
        with db():
            self.callbacks.update_status(
                str(uuid),
                JobStatus.FAILED
                if (not process.returncode == 0)
                else JobStatus.SUCCESS,
                None,
                None,
            )

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        return "Test\nxdfgdfgpkdlfxgmldfg\ndfgdf\nadzadza\nadzadza\nzdazdazd\nadazdazdaz\nezfazdzad\nadzadzadza\nadzahdizoa\nzadza\nadzadza\nadzad\nazdazd\nazdazd\nazdazd" \
               "\ndfgdf\nadzadza\nadzadza\nzdazdazd\nadazdazdaz\nezfazdzad\nadzadzadza\nadzahdizoa\nzadza\nadzadza\nadzad\nazdazd\nazdazd\nazdazd" \
               "\ndfgdf\nadzadza\nadzadza\nzdazdazd\nadazdazdaz\nezfazdzad\nadzadzadza\nadzahdizoa\nzadza\nadzadza\nadzad\nazdazd\nazdazd\nazdazd"
