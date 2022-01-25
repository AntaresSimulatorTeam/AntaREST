import logging
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4

from antarest.core.config import Config
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.model import JobStatus, LogType
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


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
        self.tmpdir = config.storage.tmp_dir
        self.job_id_to_study_id: Dict[str, Tuple[str, Path]] = {}

    def run_study(
        self,
        study_uuid: str,
        version: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> UUID:
        if self.config.launcher.local is None:
            raise LauncherInitException()

        antares_solver_path = self.config.launcher.local.binaries[version]
        if antares_solver_path is None:
            raise StudyVersionNotSupported()
        else:
            uuid = uuid4()
            export_path = Path(
                tempfile.mkdtemp(prefix="local_launch_", dir=str(self.tmpdir))
            )
            self.job_id_to_study_id[str(uuid)] = (study_uuid, export_path)
            self.storage_service.export_study_flat(
                study_uuid, params, export_path, outputs=False
            )
            self.callbacks.after_export_flat(
                str(uuid), study_uuid, export_path, launcher_parameters
            )
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(self, antares_solver_path, export_path, uuid),
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
        study_id, launch_path = self.job_id_to_study_id[str(uuid)]
        try:
            self._import_output(study_id, launch_path)
        except Exception as e:
            logger.error(
                f"Failed to import output for study {study_id} located at {launch_path}",
                exc_info=e,
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

    def _import_output(
        self, study_id: str, study_launch_path: Path
    ) -> Optional[str]:
        return self.storage_service.import_output(
            study_id,
            study_launch_path / "output",
            params=RequestParameters(DEFAULT_ADMIN_USER),
        )

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        raise NotImplementedError()

    def kill_job(self, job_id: str) -> None:
        raise NotImplementedError()
