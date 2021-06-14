import argparse
import glob
import logging
import os
import shutil
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Callable, List, Optional, Dict
from uuid import UUID, uuid4
from zipfile import ZipFile, ZIP_DEFLATED

from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters, run_with
from antareslauncher.main_option_parser import (
    MainOptionParser,
    MainOptionsParameters,
)
from antareslauncher.study_dto import StudyDTO
from antarest.common.config import Config
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import RequestParameters
from antarest.common.roles import RoleType
from antarest.common.utils.fastapi_sqlalchemy import db
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.model import JobStatus
from antarest.storage.service import StorageService

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")


class SlurmLauncher(ILauncher):
    def __init__(
        self, config: Config, storage_service: StorageService
    ) -> None:
        super().__init__(config, storage_service)
        self.callbacks: List[Callable[[str, JobStatus, bool], None]] = []
        self.check_state: bool = True
        self.thread: Optional[threading.Thread] = None
        self.job_id_to_study_id: Dict[str, str] = {}

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

    def add_callback(
        self, callback: Callable[[str, JobStatus, bool], None]
    ) -> None:
        self.callbacks.append(callback)

    def _init_launcher_arguments(self) -> argparse.Namespace:
        main_options_parameters = MainOptionsParameters(
            default_wait_time=self.config.launcher.slurm.default_wait_time,
            default_time_limit=self.config.launcher.slurm.default_time_limit,
            default_n_cpu=self.config.launcher.slurm.default_n_cpu,
            studies_in_dir=str(
                (
                    Path(self.config.launcher.slurm.local_workspace)
                    / "STUDIES_IN"
                )
            ),
            log_dir=str(
                (Path(self.config.launcher.slurm.local_workspace) / "LOGS")
            ),
            finished_dir=str(
                (Path(self.config.launcher.slurm.local_workspace) / "OUTPUT")
            ),
            ssh_config_file_is_required=False,
            ssh_configfile_path_prod_cwd=None,
            ssh_configfile_path_prod_user=None,
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
            json_dir=self.config.launcher.slurm.local_workspace,
            default_json_db_name=self.config.launcher.slurm.default_json_db_name,
            slurm_script_path=self.config.launcher.slurm.slurm_script_path,
            antares_versions_on_remote_server=self.config.launcher.slurm.antares_versions_on_remote_server,
            default_ssh_dict_from_embedded_json={
                "username": self.config.launcher.slurm.username,
                "hostname": self.config.launcher.slurm.hostname,
                "port": self.config.launcher.slurm.port,
                "private_key_file": self.config.launcher.slurm.private_key_file,
                "key_password": self.config.launcher.slurm.key_password,
                "password": self.config.launcher.slurm.password,
            },
            db_primary_key="name",
        )
        return main_parameters

    @staticmethod
    def _delete_study(study_path: Path) -> None:
        shutil.rmtree(study_path)

    def _callback(
        self, study_name: str, status: JobStatus, with_error: bool = False
    ) -> None:
        for callback in self.callbacks:
            callback(study_name, status, with_error)

    def _export_output(self, output_path: Path) -> BytesIO:
        data = BytesIO()
        zipf = ZipFile(data, "w", ZIP_DEFLATED)
        current_dir = os.getcwd()
        os.chdir(output_path)
        for path in glob.glob("**", recursive=True):
            zipf.write(path, path)
        zipf.close()
        os.chdir(current_dir)
        data.seek(0)
        return data

    def _import_study_output(self, job_id: str) -> None:
        study_id = self.job_id_to_study_id[job_id]

        output = self._export_output(
            self.config.launcher.slurm.local_workspace
            / "OUTPUT"
            / job_id
            / "output"
        )

        self.storage_service.import_output(
            study_id,
            output,
            params=RequestParameters(
                JWTUser(
                    id=1,
                    impersonator=1,
                    type="users",
                    groups=[
                        JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
                    ],
                )
            ),
        )

    def _check_studies_state(self) -> None:
        arguments = self._init_launcher_arguments()
        antares_launcher_parameters = self._init_launcher_parameters()

        run_with(
            arguments=arguments,
            parameters=antares_launcher_parameters,
            show_banner=False,
        )

        data_repo_tinydb = DataRepoTinydb(
            database_name=(
                antares_launcher_parameters.json_dir
                / antares_launcher_parameters.default_json_db_name
            ),
            db_primary_key=antares_launcher_parameters.db_primary_key,
        )

        study_list = data_repo_tinydb.get_list_of_studies()

        all_done = True

        for study in study_list:
            all_done = all_done and (study.finished or study.with_error)
            if study.finished or study.with_error:
                with db():
                    job_id = self.job_id_to_study_id.get(study.name, None)
                    if job_id is not None:
                        self._callback(
                            job_id,
                            JobStatus.FAILED
                            if study.with_error
                            else JobStatus.SUCCESS,
                            study.with_error,
                        )
                        self._import_study_output(study.name)
                    else:
                        # should not happen
                        logger.warning(
                            f"Failed to retrieve job id from study {study.name}"
                        )
                data_repo_tinydb.remove_study(study.name)
                self._delete_study(
                    self.config.launcher.slurm.local_workspace
                    / "OUTPUT"
                    / study.name
                )
                del self.job_id_to_study_id[study.name]

        if all_done:
            self.stop()

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:  # TODO: version ?
        arguments = self._init_launcher_arguments()
        antares_launcher_parameters = self._init_launcher_parameters()

        launch_uuid = uuid4()

        # TODO do this in a thread and directly return the job id
        study_path = Path(arguments.studies_in) / str(launch_uuid)

        self.job_id_to_study_id[str(launch_uuid)] = study_uuid

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
