from typing import Dict

from antarest.common.config import Config
from antarest.launcher.business.ilauncher import ILauncher
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)


class FactoryLauncher:
    def build_launcher(self, config: Config) -> Dict[str, ILauncher]:
        dict_launchers = dict()
        if config["launcher.local"]:
            dict_launchers["local"] = LocalLauncher(config)
        if config["launcher.slurm"]:
            dict_launchers["slurm"] = SlurmLauncher(config)
        if not dict_launchers:
            raise NotImplementedError
        else:
            return dict_launchers
