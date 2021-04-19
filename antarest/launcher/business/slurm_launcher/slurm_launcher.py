from pathlib import Path
from typing import Callable, List
from uuid import UUID

from antarest.common.config import Config
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher import (
    definitions,
)
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher.main import (
    run_with,
)
from antarest.launcher.business.slurm_launcher.antares_launcher.antareslauncher.main_option_parser import (
    MainOptionParser,
    look_for_default_ssh_conf_file,
)
from antarest.launcher.model import JobResult


class SlurmLauncher(ILauncher):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
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

    def run_study(self, study_path: Path, version: str) -> UUID:
        arguments = self._init_launcher_arguments()

        # export study

        run_with(arguments)

        # delete exported study
