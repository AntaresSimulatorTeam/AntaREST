from uuid import UUID

from antarest.common.config import Config
from antarest.launcher.factory_launcher import FactoryLauncher
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.repository import JobResultRepository
from antarest.storage.service import StorageService


class JobNotFound(Exception):
    pass


class LauncherService:
    def __init__(
        self,
        config: Config,
        storage_service: StorageService,
        repository: JobResultRepository,
        factory_launcher: FactoryLauncher = FactoryLauncher(),
    ) -> None:
        self.config = config
        self.storage_service = storage_service
        self.repository = repository
        self.launcher = factory_launcher.build_launcher(config)
        self.launcher.add_callback(self.update)

    def update(self, job_result: JobResult) -> None:
        self.repository.save(job_result)

    def run_study(self, study_uuid: str) -> UUID:
        study_info = self.storage_service.get_study_information(
            uuid=study_uuid
        )
        study_version = study_info["antares"]["version"]
        study_path = self.storage_service.get_study_path(study_uuid)
        job_uuid: UUID = self.launcher.run_study(study_path, study_version)

        self.repository.save(
            JobResult(id=str(job_uuid), job_status=JobStatus.RUNNING)
        )

        return job_uuid

    def get_result(self, job_uuid: UUID) -> JobResult:
        job_result = self.repository.get(str(job_uuid))
        if job_result:
            return job_result

        raise JobNotFound()
