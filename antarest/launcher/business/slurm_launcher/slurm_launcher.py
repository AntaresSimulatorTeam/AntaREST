import os

from pathlib import Path
from typing import Callable, List
from uuid import UUID

from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher import (
    definitions,
)
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher.main import (
    run_with,
    MainParameters,
)
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher.main_option_parser import (
    MainOptionParser,
    look_for_default_ssh_conf_file,
)
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
        parser: MainOptionParser = MainOptionParser()
        parser.add_basic_arguments()
        parser.add_advanced_arguments()
        arguments = parser.parse_args()

        arguments.wait_mode = False
        arguments.wait_time = definitions.DEFAULT_WAIT_TIME
        arguments.studies_in = str(
            (Path(self.config["launcher.slurm.workspace"]) / "STUDIES_IN")
        )
        arguments.output_dir = str(
            (Path(self.config["launcher.slurm.workspace"]) / "OUTPUT")
        )
        arguments.check_queue = False
        arguments.time_limit = definitions.DEFAULT_TIME_LIMIT
        arguments.json_ssh_config = look_for_default_ssh_conf_file()
        arguments.log_dir = str(
            (Path(self.config["launcher.slurm.workspace"]) / "logs")
        )
        arguments.n_cpu = definitions.DEFAULT_N_CPU
        arguments.job_id_to_kill = None
        arguments.xpansion_mode = False
        arguments.version = False
        arguments.post_processing = False
        return arguments

    def _init_launcher_parameters(self) -> MainParameters:
        main_parameters = MainParameters(json_dir=,default_json_db_name=,slurm_script_path=,antares_versions_on_remote_server=,default_ssh_dict_from_embedded_json=,db_primary_key=)
        pass

    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:
        arguments = self._init_launcher_arguments()
        main_antares_launcher_parameters = self._init_launcher_parameters()

        # export study
        self._export_study_to_studies_in_directory(
            study_uuid, arguments.studies_in, params
        )

        run_with(arguments)

        self._delete_input_study()

        # delete exported study

    def _export_study_to_studies_in_directory(
        self,
        study_uuid: str,
        studies_in_directory: str,
        params: RequestParameters,
    ):
        zip_data = self.storage_service.export_study(
            uuid=study_uuid, params=params, compact=False, outputs=False
        )
        os.makedirs(studies_in_directory, exist_ok=True)

        zipfile_path = studies_in_directory + "/study.zip"
        with open(zipfile_path, "wb") as f:
            f.write(zip_data.getvalue())

        import zipfile

        with zipfile.ZipFile(zipfile_path, "r") as zip_ref:
            zip_ref.extractall(studies_in_directory)

    def _delete_input_study(self):
        pass
