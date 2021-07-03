from datetime import datetime
from http import HTTPStatus
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
)
from antarest.common.requests import (
    RequestParameters,
)
from antarest.launcher.business.factory_launcher import FactoryLauncher
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.repository import JobResultRepository
from antarest.storage.service import StorageService


class JobNotFound(Exception):
    pass


class LauncherServiceNotAvailableException(HTTPException):
    def __init__(self, engine: str):
        super(LauncherServiceNotAvailableException, self).__init__(
            HTTPStatus.BAD_REQUEST, f"The engine {engine} is not available"
        )


class LauncherService:
    def __init__(
        self,
        config: Config,
        storage_service: StorageService,
        repository: JobResultRepository,
        event_bus: IEventBus,
        factory_launcher: FactoryLauncher = FactoryLauncher(),
    ) -> None:
        self.config = config
        self.storage_service = storage_service
        self.repository = repository
        self.event_bus = event_bus
        self.launchers = factory_launcher.build_launcher(
            config, storage_service, event_bus
        )
        for _, launcher in self.launchers.items():
            launcher.add_statusupdate_callback(self.update)

    def get_launchers(self) -> List[str]:
        return list(self.launchers.keys())

    def update(self, job_uuid: str, status: JobStatus) -> None:
        job_result = self.repository.get(job_uuid)
        if job_result is not None:
            job_result.job_status = status
            final_status = status in [JobStatus.SUCCESS, JobStatus.FAILED]
            if final_status:
                job_result.completion_date = datetime.utcnow()
            self.repository.save(job_result)
            self.event_bus.push(
                Event(
                    EventType.STUDY_JOB_COMPLETED
                    if final_status
                    else EventType.STUDY_JOB_STATUS_UPDATE,
                    {"jid": str(job_result.id), "sid": job_result.study_id},
                )
            )

    def run_study(
        self, study_uuid: str, params: RequestParameters, launcher: str
    ) -> UUID:
        study_info = self.storage_service.get_study_information(
            uuid=study_uuid, params=params
        )
        study_version = study_info.version
        if launcher not in self.launchers:
            raise LauncherServiceNotAvailableException(launcher)
        job_uuid: UUID = self.launchers[launcher].run_study(
            study_uuid, str(study_version), params
        )

        self.repository.save(
            JobResult(
                id=str(job_uuid),
                study_id=study_uuid,
                job_status=JobStatus.PENDING,
            )
        )
        self.event_bus.push(
            Event(
                EventType.STUDY_JOB_STARTED,
                {"jid": str(job_uuid), "sid": study_uuid},
            )
        )

        return job_uuid

    def get_result(self, job_uuid: UUID) -> JobResult:
        job_result = self.repository.get(str(job_uuid))
        if job_result:
            return job_result

        raise JobNotFound()

    def get_jobs(self, study_uid: Optional[str] = None) -> List[JobResult]:
        if study_uid is not None:
            job_results = self.repository.find_by_study(study_uid)
        else:
            job_results = self.repository.get_all()
        return job_results
