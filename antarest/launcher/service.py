from datetime import datetime
from http import HTTPStatus
from typing import List, Optional, cast
from uuid import UUID

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
)
from antarest.core.requests import (
    RequestParameters,
)
from antarest.launcher.business.abstractlauncher import LauncherCallbacks
from antarest.launcher.business.factory_launcher import FactoryLauncher
from antarest.launcher.model import JobResult, JobStatus, LogType
from antarest.launcher.repository import JobResultRepository
from antarest.storage.service import StorageService


class JobNotFound(HTTPException):
    def __init__(self) -> None:
        super(JobNotFound, self).__init__(HTTPStatus.NOT_FOUND)


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
            config,
            storage_service,
            LauncherCallbacks(
                update_status=lambda jobid, status, msg, output_id: self.update(
                    jobid, status, msg, output_id
                )
            ),
            event_bus,
        )

    def get_launchers(self) -> List[str]:
        return list(self.launchers.keys())

    def update(
        self,
        job_uuid: str,
        status: JobStatus,
        msg: Optional[str],
        output_id: Optional[str],
    ) -> None:
        job_result = self.repository.get(job_uuid)
        if job_result is not None:
            job_result.job_status = status
            job_result.msg = msg
            job_result.output_id = output_id
            final_status = status in [JobStatus.SUCCESS, JobStatus.FAILED]
            if final_status:
                job_result.completion_date = datetime.utcnow()
            self.repository.save(job_result)
            self.event_bus.push(
                Event(
                    EventType.STUDY_JOB_COMPLETED
                    if final_status
                    else EventType.STUDY_JOB_STATUS_UPDATE,
                    job_result.to_dict(),
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

        job_status = JobResult(
            id=str(job_uuid),
            study_id=study_uuid,
            job_status=JobStatus.PENDING,
            launcher=launcher,
        )
        self.repository.save(job_status)
        self.event_bus.push(
            Event(
                EventType.STUDY_JOB_STARTED,
                job_status.to_dict(),
            )
        )

        return job_uuid

    def get_result(
        self, job_uuid: UUID, params: RequestParameters
    ) -> JobResult:
        job_result = self.repository.get(str(job_uuid))
        if job_result:
            return job_result

        raise JobNotFound()

    def get_jobs(
        self, study_uid: Optional[str], params: RequestParameters
    ) -> List[JobResult]:
        if study_uid is not None:
            job_results = self.repository.find_by_study(study_uid)
        else:
            job_results = self.repository.get_all()
        return job_results

    def get_log(
        self, job_id: str, log_type: LogType, params: RequestParameters
    ) -> Optional[str]:
        job_result = self.repository.get(str(job_id))
        if job_result:
            if job_result.output_id:
                return cast(
                    str,
                    self.storage_service.get(
                        job_result.study_id,
                        f"/output/{job_result.output_id}/simulation",
                        depth=1,
                        params=params,
                    ),
                )
            if job_result.launcher not in self.launchers:
                raise LauncherServiceNotAvailableException(job_result.launcher)
            return self.launchers[job_result.launcher].get_log(
                job_id, log_type
            )
        raise JobNotFound()
