import logging
from typing import Dict

from antarest.common.config import Config
from antarest.launcher.business.ilauncher import (
    ILauncher,
    LauncherInitException,
)
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.storage.service import StorageService

logger = logging.getLogger(__name__)


class FactoryLauncher:
    def build_launcher(
        self, config: Config, storage_service: StorageService
    ) -> Dict[str, ILauncher]:
        dict_launchers: Dict[str, ILauncher] = dict()
        if config.launcher.local is not None:
            dict_launchers["local"] = LocalLauncher(config, storage_service)
        if config.launcher.slurm is not None:
            dict_launchers["slurm"] = SlurmLauncher(config, storage_service)
        return dict_launchers
