from pathlib import Path
from typing import Callable, List
from uuid import UUID

from antareslauncher.main import MainParameters, run_with
from antareslauncher.main_option_parser import (
    MainOptionParser,
    MainOptionsParameters,
)
from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.model import JobResult
from antarest.storage.service import StorageService


class SlurmLauncher(ILauncher):
    def __init__(
        self, config: Config, storage_service: StorageService
    ) -> None:
        super().__init__(config, storage_service)
        self.callbacks: List[Callable[[JobResult], None]] = []

    def add_callback(self, callback: Callable[[JobResult], None]) -> None:
        self.callbacks.append(callback)

    def _init_launcher_arguments(self):
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
        arguments = parser.parse_args()

        arguments.wait_mode = False
        arguments.check_queue = False
        arguments.json_ssh_config = None
        arguments.log_dir = str(
            (Path(self.config.launcher.slurm.local_workspace / "logs"))
        )
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
            db_primary_key=self.config.launcher.slurm.db_primary_key,
        )
        return main_parameters

    def _export_study_to_studies_in_directory(
        self,
        study_uuid: str,
        studies_in_directory: str,
        params: RequestParameters,
    ):
        pass

    def _delete_input_study(self):
        pass

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:
        arguments = self._init_launcher_arguments()
        antares_launcher_parameters = self._init_launcher_parameters()

        # export study
        self._export_study_to_studies_in_directory(
            study_uuid, arguments.studies_in, params
        )

        run_with(arguments, antares_launcher_parameters)

        self._delete_input_study()

        # delete exported study
