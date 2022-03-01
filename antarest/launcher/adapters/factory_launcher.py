import logging
from typing import Dict

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherCallbacks,
)
from antarest.launcher.adapters.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class FactoryLauncher:
    def build_launcher(
        self,
        config: Config,
        storage_service: StudyService,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ) -> Dict[str, AbstractLauncher]:
        dict_launchers: Dict[str, AbstractLauncher] = dict()
        if config.launcher.local is not None:
            dict_launchers["local"] = LocalLauncher(
                config, storage_service, callbacks, event_bus
            )
        if config.launcher.slurm is not None:
            dict_launchers["slurm"] = SlurmLauncher(
                config,
                storage_service,
                callbacks,
                event_bus,
                retrieve_existing_jobs=True,
            )
        return dict_launchers
