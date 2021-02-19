from uuid import UUID

from antarest.common.config import Config
from antarest.launcher.factory_launcher import FactoryLauncher
from antarest.launcher.model import ExecutionResult
from antarest.storage.service import StorageService


class LauncherService:
    def __init__(
        self,
        config: Config,
        storage_service: StorageService,
        factory_launcher=FactoryLauncher,
    ) -> None:
        self.config = config
        self.storage_service = storage_service
        self.launcher = factory_launcher.build_launcher(config)

    def run_study(self, study_uuid: str) -> UUID:
        study_info = self.storage_service.get_study_information(
            uuid=study_uuid
        )
        study_version = study_info["antares"]["version"]
        study_path = self.storage_service.get_study_path(study_uuid)
        job_uuid = self.launcher.run_study(study_path, study_version)
        return job_uuid

    def get_result(self, job_uuid: UUID) -> ExecutionResult:
        return self.launcher.get_result(uuid=job_uuid)
