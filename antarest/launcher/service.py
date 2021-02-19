from antarest.common.config import Config
from antarest.launcher.factory_launcher import FactoryLauncher
from antarest.storage.service import StorageService


class LauncherService:
    def __init__(
        self, config: Config, storage_service: StorageService
    ) -> None:
        self.config = config
        self.storage_service = storage_service
        self.launcher = FactoryLauncher.build_launcher(config)

    def run_study(self):
        self.launcher.run_study(study_path, version)

    def get_status(self):
        self.launcher.get_result()
