from antarest.common.config import Config


class FactoryLauncher:
    @staticmethod
    def build_launcher(config: Config) -> ILauncher:
        if config["launcher.type"] == "local":
            return LocalLauncher()
        else:
            raise NotImplementedError
