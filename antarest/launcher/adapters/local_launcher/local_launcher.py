import logging
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from multiprocessing import Process
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable, cast, IO
from uuid import UUID, uuid4

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LogType
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class StudyVersionNotSupported(Exception):
    pass


class LocalLauncher(AbstractLauncher):
    """
    This local launcher is meant to work when using AntaresWeb on a single worker process in local mode
    """

    def __init__(
        self,
        config: Config,
        storage_service: StudyService,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ) -> None:
        super().__init__(config, storage_service, callbacks, event_bus)
        self.tmpdir = config.storage.tmp_dir
        self.job_id_to_study_id: Dict[  # type: ignore
            str, Tuple[str, Path, subprocess.Popen]
        ] = {}
        self.logs: Dict[str, str] = {}

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
            job = threading.Thread(
                target=LocalLauncher._compute,
                args=(
                    self,
                    antares_solver_path,
                    study_uuid,
                    uuid,
                    launcher_parameters,
                ),
            )
            job.start()
            return uuid

    def _compute(
        self,
        antares_solver_path: Path,
        study_uuid: str,
        uuid: UUID,
        launcher_parameters: Optional[JSON],
    ) -> None:
        end = False

        def stop_reading_output() -> bool:
            if end and str(uuid) in self.logs:
                del self.logs[str(uuid)]
            return end

        tmp_path = tempfile.mkdtemp(
            prefix="local_launch_", dir=str(self.tmpdir)
        )
        export_path = Path(tmp_path) / "export"
        try:
            with db():
                self.storage_service.export_study_flat(
                    study_uuid,
                    RequestParameters(DEFAULT_ADMIN_USER),
                    export_path,
                    outputs=False,
                )
                self.callbacks.after_export_flat(
                    str(uuid), study_uuid, export_path, launcher_parameters
                )

            process = subprocess.Popen(
                [antares_solver_path, export_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
            )
            self.job_id_to_study_id[str(uuid)] = (
                study_uuid,
                export_path,
                process,
            )
            with db():
                self.callbacks.update_status(
                    str(uuid),
                    JobStatus.RUNNING,
                    None,
                    None,
                )

            thread = threading.Thread(
                target=lambda: LogTailManager.follow(
                    cast(IO[str], process.stdout),
                    self.create_update_log(str(uuid), study_uuid),
                    stop_reading_output,
                    None,
                ),
                daemon=True,
            )
            thread.start()

            while True:
                if process.poll() is not None:
                    break
                time.sleep(1)

            if launcher_parameters is not None:
                post_processing = launcher_parameters.get(
                    "post_processing", False
                )
                if (
                    isinstance(post_processing, bool) and post_processing
                ) or launcher_parameters.get(
                    "adequacy_patch", None
                ) is not None:
                    subprocess.run(
                        ["Rscript", "post-processing.R"], cwd=export_path
                    )

            try:
                with db():
                    output_id = self._import_output(study_uuid, export_path)
            except Exception as e:
                logger.error(
                    f"Failed to import output for study {study_uuid} located at {export_path}",
                    exc_info=e,
                )
            del self.job_id_to_study_id[str(uuid)]
            with db():
                self.callbacks.update_status(
                    str(uuid),
                    JobStatus.FAILED
                    if (not process.returncode == 0) or not output_id
                    else JobStatus.SUCCESS,
                    None,
                    output_id,
                )
        except Exception as e:
            logger.error(
                f"Unexpected error happend during launch {uuid}", exc_info=e
            )
            self.callbacks.update_status(
                str(uuid),
                JobStatus.FAILED,
                str(e),
                None,
            )
        finally:
            logger.info(f"Removing launch {uuid} export path at {tmp_path}")
            end = True
            shutil.rmtree(tmp_path)

    def _import_output(
        self, study_id: str, study_launch_path: Path
    ) -> Optional[str]:
        return self.storage_service.import_output(
            study_id,
            study_launch_path / "output",
            params=RequestParameters(DEFAULT_ADMIN_USER),
        )

    def create_update_log(
        self, job_id: str, study_id: str
    ) -> Callable[[str], None]:
        base_func = super().create_update_log(job_id, study_id)
        self.logs[job_id] = ""

        def append_to_log(log_line: str) -> None:
            base_func(log_line)
            self.logs[job_id] += log_line + "\n"

        return append_to_log

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        if job_id in self.job_id_to_study_id and job_id in self.logs:
            return self.logs[job_id]
        return None

    def kill_job(self, job_id: str) -> None:
        if job_id in self.job_id_to_study_id:
            return self.job_id_to_study_id[job_id][2].send_signal(
                signal.SIGTERM
            )
        else:
            self.callbacks.update_status(
                job_id,
                JobStatus.FAILED,
                None,
                None,
            )
