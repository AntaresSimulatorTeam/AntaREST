from antarest.common.config import Config
from antarest.launcher.ilauncher import ILauncher
from antarest.launcher.local_launcher import LocalLauncher


class FactoryLauncher:
    def build_launcher(self, config: Config) -> ILauncher:
        if config["launcher.type"] == "local":
            return LocalLauncher(config)
        else:
            raise NotImplementedError
