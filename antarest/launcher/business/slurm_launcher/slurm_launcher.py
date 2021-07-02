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

from antarest.common.config import Config, SlurmConfig
from antarest.common.jwt import DEFAULT_ADMIN_USER
from antarest.common.requests import RequestParameters
from antarest.common.utils.fastapi_sqlalchemy import db
from antarest.launcher.business.ilauncher import (
    ILauncher,
    LauncherInitException,
)
from antarest.launcher.model import JobStatus
from antarest.storage.service import StorageService

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")


class SlurmLauncher(ILauncher):
    def __init__(
        self, config: Config, storage_service: StorageService
    ) -> None:
        super().__init__(config, storage_service)
        if config.launcher.slurm is None:
            raise LauncherInitException()

        self.slurm_config: SlurmConfig = config.launcher.slurm
        self.check_state: bool = True
        self.thread: Optional[threading.Thread] = None
        self.job_id_to_study_id: Dict[str, str] = {}

    def _loop(self) -> None:
        arguments = self._init_launcher_arguments()
        antares_launcher_parameters = self._init_launcher_parameters()
        data_repo_tinydb = DataRepoTinydb(
            database_name=(
                antares_launcher_parameters.json_dir
                / antares_launcher_parameters.default_json_db_name
            ),
            db_primary_key=antares_launcher_parameters.db_primary_key,
        )
        while self.check_state:
            self._check_studies_state(
                arguments, antares_launcher_parameters, data_repo_tinydb
            )
            time.sleep(2)

    def start(self) -> None:
        self.check_state = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.check_state = False
        self.thread = None

    def add_statusupdate_callback(
        self, callback: Callable[[str, JobStatus, bool], None]
    ) -> None:
        self.callbacks.append(callback)

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

    def _callback(
        self, study_name: str, status: JobStatus, with_error: bool = False
    ) -> None:
        for callback in self.callbacks:
            callback(study_name, status, with_error)

    def _import_study_output(self, job_id: str) -> None:
        study_id = self.job_id_to_study_id[job_id]

        zipped_output = str(
            self.slurm_config.local_workspace / "OUTPUT" / job_id / "output"
        )
        shutil.make_archive(
            zipped_output,
            "zip",
            self.slurm_config.local_workspace / "OUTPUT" / job_id / "output",
        )

        with open(zipped_output + ".zip", "rb") as fh:
            self.storage_service.import_output(
                study_id,
                fh,
                params=RequestParameters(DEFAULT_ADMIN_USER),
            )

    def _check_studies_state(
        self,
        arguments: argparse.Namespace,
        antares_launcher_parameters: MainParameters,
        data_repo_tinydb: DataRepoTinydb,
    ) -> None:

        try:
            run_with(
                arguments=arguments,
                parameters=antares_launcher_parameters,
                show_banner=False,
            )
        except Exception as e:
            logger.info("Could not get data on remote server")

        study_list = data_repo_tinydb.get_list_of_studies()

        all_done = True

        for study in study_list:
            all_done = all_done and (study.finished or study.with_error)
            if study.finished or study.with_error:
                try:
                    with db():
                        self._callback(
                            study.name,
                            JobStatus.FAILED
                            if study.with_error
                            else JobStatus.SUCCESS,
                            study.with_error,
                        )
                        self._import_study_output(study.name)
                finally:
                    data_repo_tinydb.remove_study(study.name)
                    self._delete_study(
                        self.slurm_config.local_workspace
                        / "OUTPUT"
                        / study.name
                    )
                    del self.job_id_to_study_id[study.name]

        if all_done:
            self.stop()

    def _clean_local_workspace(self) -> None:
        logger.info("Cleaning up slurm workspace")
        local_workspace = self.slurm_config.local_workspace
        for filename in os.listdir(local_workspace):
            file_path = os.path.join(local_workspace, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:  # TODO: version ?
        arguments = self._init_launcher_arguments()
        antares_launcher_parameters = self._init_launcher_parameters()

        launch_uuid = uuid4()

        # TODO do this in a thread and directly return the job id
        study_path = Path(arguments.studies_in) / str(launch_uuid)

        self.job_id_to_study_id[str(launch_uuid)] = study_uuid

        if not self.thread:
            self._clean_local_workspace()

        # export study
        self.storage_service.export_study_flat(
            study_uuid, params, study_path, outputs=False
        )

        run_with(arguments, antares_launcher_parameters, show_banner=False)
        self._callback(str(launch_uuid), JobStatus.RUNNING)

        if not self.thread:
            self.start()

        self._delete_study(study_path)

        return launch_uuid
