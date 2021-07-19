import argparse
import logging
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Dict
from uuid import UUID, uuid4

from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters, run_with
from antareslauncher.main_option_parser import (
    MainOptionParser,
    MainOptionsParameters,
)
from antareslauncher.study_dto import StudyDTO

from antarest.core.config import Config, SlurmConfig
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LogType
from antarest.storage.service import StudyService

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")


class SlurmLauncher(AbstractLauncher):
    def __init__(
        self,
        config: Config,
        storage_service: StudyService,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ) -> None:
        super().__init__(config, storage_service, callbacks)
        if config.launcher.slurm is None:
            raise LauncherInitException()

        self.slurm_config: SlurmConfig = config.launcher.slurm
        self.check_state: bool = True
        self.event_bus = event_bus
        self.thread: Optional[threading.Thread] = None
        self.job_id_to_study_id: Dict[str, str] = {}
        self._check_config()
        self.log_tail_manager = LogTailManager(
            self.slurm_config.local_workspace
        )
        self.launcher_args = self._init_launcher_arguments()
        self.launcher_params = self._init_launcher_parameters()
        self.data_repo_tinydb = DataRepoTinydb(
            database_name=(
                self.launcher_params.json_dir
                / self.launcher_params.default_json_db_name
            ),
            db_primary_key=self.launcher_params.db_primary_key,
        )

    def _check_config(self) -> None:
        assert (
            self.slurm_config.local_workspace.exists()
            and self.slurm_config.local_workspace.is_dir()
        )  # and check write permission

    def _loop(self) -> None:
        while self.check_state:
            self._check_studies_state()
            time.sleep(2)

    def start(self) -> None:
        self.check_state = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.check_state = False
        self.thread = None

    def _init_launcher_arguments(self) -> argparse.Namespace:
        main_options_parameters = MainOptionsParameters(
            default_wait_time=self.slurm_config.default_wait_time,
            default_time_limit=self.slurm_config.default_time_limit,
            default_n_cpu=self.slurm_config.default_n_cpu,
            studies_in_dir=str(
                (Path(self.slurm_config.local_workspace) / "STUDIES_IN")
            ),
            log_dir=str((Path(self.slurm_config.local_workspace) / "LOGS")),
            finished_dir=str(
                (Path(self.slurm_config.local_workspace) / "OUTPUT")
            ),
            ssh_config_file_is_required=False,
            ssh_configfile_path_alternate1=None,
            ssh_configfile_path_alternate2=None,
        )

        parser: MainOptionParser = MainOptionParser(main_options_parameters)
        parser.add_basic_arguments()
        parser.add_advanced_arguments()
        arguments = parser.parse_args([])

        arguments.wait_mode = False
        arguments.check_queue = False
        arguments.json_ssh_config = None
        arguments.job_id_to_kill = None
        arguments.xpansion_mode = False
        arguments.version = False
        arguments.post_processing = False
        return arguments

    def _init_launcher_parameters(self) -> MainParameters:
        main_parameters = MainParameters(
            json_dir=self.slurm_config.local_workspace,
            default_json_db_name=self.slurm_config.default_json_db_name,
            slurm_script_path=self.slurm_config.slurm_script_path,
            antares_versions_on_remote_server=self.slurm_config.antares_versions_on_remote_server,
            default_ssh_dict_from_embedded_json={
                "username": self.slurm_config.username,
                "hostname": self.slurm_config.hostname,
                "port": self.slurm_config.port,
                "private_key_file": self.slurm_config.private_key_file,
                "key_password": self.slurm_config.key_password,
                "password": self.slurm_config.password,
            },
            db_primary_key="name",
        )
        return main_parameters

    def _delete_study(self, study_path: Path) -> None:
        if (
            self.slurm_config.local_workspace.absolute()
            in study_path.absolute().parents
        ):
            shutil.rmtree(study_path)

    def _import_study_output(self, job_id: str) -> Optional[str]:
        study_id = self.job_id_to_study_id[job_id]
        return self.storage_service.import_output(
            study_id,
            self.slurm_config.local_workspace / "OUTPUT" / job_id / "output",
            params=RequestParameters(DEFAULT_ADMIN_USER),
        )

    def _check_studies_state(self) -> None:
        try:
            run_with(
                arguments=self.launcher_args,
                parameters=self.launcher_params,
                show_banner=False,
            )
        except Exception as e:
            logger.info("Could not get data on remote server")

        study_list = self.data_repo_tinydb.get_list_of_studies()

        all_done = True

        for study in study_list:
            if study.name not in self.job_id_to_study_id:
                # this job is handled by another worker process
                continue

            all_done = all_done and (study.finished or study.with_error)
            if study.finished or study.with_error:
                try:
                    self.log_tail_manager.stop_tracking(
                        SlurmLauncher._get_log_path(study)
                    )
                    with db():
                        output_id = self._import_study_output(study.name)
                        self.callbacks.update_status(
                            study.name,
                            JobStatus.FAILED
                            if study.with_error
                            else JobStatus.SUCCESS,
                            None,
                            output_id,
                        )

                finally:
                    self.data_repo_tinydb.remove_study(study.name)
                    self._delete_study(
                        self.slurm_config.local_workspace
                        / "OUTPUT"
                        / study.name
                    )
                    del self.job_id_to_study_id[study.name]
            else:
                self.log_tail_manager.track(
                    SlurmLauncher._get_log_path(study),
                    self.create_update_log(
                        study.name, self.job_id_to_study_id[study.name]
                    ),
                )

        if all_done:
            self.stop()

    def create_update_log(
        self, job_id: str, study_id: str
    ) -> Callable[[str], None]:
        def update_log(log_line: str) -> None:
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_LOG_UPDATE,
                    payload={
                        "log": log_line,
                        "job_id": job_id,
                        "study_id": study_id,
                    },
                )
            )

        return update_log

    @staticmethod
    def _get_log_path(
        study: StudyDTO, log_type: LogType = LogType.STDOUT
    ) -> Optional[Path]:
        log_dir = Path(study.job_log_dir)
        log_prefix = (
            "antares-out-" if log_type == LogType.STDOUT else "antares-err-"
        )
        if log_dir.exists() and log_dir.is_dir():
            for fname in os.listdir(log_dir):
                if fname.startswith(log_prefix):
                    return log_dir / fname
        return None

    def _clean_local_workspace(self) -> None:
        logger.info("Cleaning up slurm workspace")
        local_workspace = self.slurm_config.local_workspace
        for filename in os.listdir(local_workspace):
            file_path = os.path.join(local_workspace, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def _run_study(
        self, study_uuid: str, launch_uuid: str, params: RequestParameters
    ) -> None:
        with db():
            study_path = Path(self.launcher_args.studies_in) / str(launch_uuid)

            self.job_id_to_study_id[str(launch_uuid)] = study_uuid

            if not self.thread:
                self._clean_local_workspace()

            # export study
            self.storage_service.export_study_flat(
                study_uuid, params, study_path, outputs=False
            )

            run_with(
                self.launcher_args, self.launcher_params, show_banner=False
            )
            self.callbacks.update_status(
                str(launch_uuid), JobStatus.RUNNING, None, None
            )

            if not self.thread:
                self.start()

            self._delete_study(study_path)

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:  # TODO: version ?
        launch_uuid = uuid4()

        thread = threading.Thread(
            target=self._run_study, args=(study_uuid, launch_uuid, params)
        )
        thread.start()

        return launch_uuid

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                log_path = SlurmLauncher._get_log_path(study, log_type)
                if log_path:
                    return log_path.read_text()
        return None
