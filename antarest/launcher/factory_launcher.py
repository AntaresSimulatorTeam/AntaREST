from antarest.common.config import Config
from antarest.launcher.ilauncher import ILauncher
from antarest.launcher.local_launcher import LocalLauncher


class FactoryLauncher:
    @staticmethod
    def build_launcher(config: Config) -> ILauncher:
        if config["launcher.type"] == "local":
            return LocalLauncher(config)
        else:
            raise NotImplementedError
