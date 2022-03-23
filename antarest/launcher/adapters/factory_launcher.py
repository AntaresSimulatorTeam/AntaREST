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
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)

logger = logging.getLogger(__name__)


class FactoryLauncher:
    def build_launcher(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        study_factory: StudyFactory,
    ) -> Dict[str, AbstractLauncher]:
        dict_launchers: Dict[str, AbstractLauncher] = dict()
        if config.launcher.local is not None:
            dict_launchers["local"] = LocalLauncher(
                config, callbacks, event_bus
            )
        if config.launcher.slurm is not None:
            dict_launchers["slurm"] = SlurmLauncher(
                config,
                callbacks,
                event_bus,
                study_factory,
                retrieve_existing_jobs=True,
            )
        return dict_launchers
