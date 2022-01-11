import logging
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional, cast, Dict
from uuid import UUID

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
    EventChannelDirectory,
)
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.launcher.adapters.abstractlauncher import LauncherCallbacks
from antarest.launcher.adapters.factory_launcher import FactoryLauncher
from antarest.launcher.model import JobResult, JobStatus, LogType
from antarest.launcher.repository import JobResultRepository
from antarest.study.service import StudyService
from antarest.core.model import (
    StudyPermissionType,
    PermissionInfo,
    JSON,
)
from antarest.study.storage.utils import (
    assert_permission,
    create_permission_from_study,
)

logger = logging.getLogger(__name__)


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
        study_service: StudyService,
        job_result_repository: JobResultRepository,
        event_bus: IEventBus,
        factory_launcher: FactoryLauncher = FactoryLauncher(),
    ) -> None:
        self.config = config
        self.study_service = study_service
        self.job_result_repository = job_result_repository
        self.event_bus = event_bus
        self.launchers = factory_launcher.build_launcher(
            config,
            study_service,
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
        logger.info(f"Setting study with job id {job_uuid} status to {status}")
        job_result = self.job_result_repository.get(job_uuid)
        if job_result is not None:
            job_result.job_status = status
            job_result.msg = msg
            job_result.output_id = output_id
            final_status = status in [JobStatus.SUCCESS, JobStatus.FAILED]
            if final_status:
                job_result.completion_date = datetime.utcnow()
            self.job_result_repository.save(job_result)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_COMPLETED
                    if final_status
                    else EventType.STUDY_JOB_STATUS_UPDATE,
                    payload=job_result.to_dto().dict(),
                    channel=EventChannelDirectory.JOB_STATUS + job_result.id,
                )
            )
        logger.info(f"Study status set")

    def _assert_launcher_is_initialized(self, launcher: str) -> None:
        if launcher not in self.launchers:
            raise LauncherServiceNotAvailableException(launcher)

    def run_study(
        self,
        study_uuid: str,
        launcher: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> UUID:
        study_info = self.study_service.get_study_information(
            uuid=study_uuid, params=params
        )
        study_version = study_info.version

        self._assert_launcher_is_initialized(launcher)

        job_uuid: UUID = self.launchers[launcher].run_study(
            study_uuid, str(study_version), launcher_parameters, params
        )

        job_status = JobResult(
            id=str(job_uuid),
            study_id=study_uuid,
            job_status=JobStatus.PENDING,
            launcher=launcher,
        )
        self.job_result_repository.save(job_status)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_JOB_STARTED,
                payload=job_status.to_dto().dict(),
                permissions=create_permission_from_study(study_info),
            )
        )

        return job_uuid

    def kill_job(self, job_id: str, params: RequestParameters) -> JobResult:

        job_result = self.job_result_repository.get(job_id)
        assert job_result
        study_uuid = job_result.study_id
        launcher = job_result.launcher
        study = self.study_service.get_study(study_uuid)
        assert_permission(
            user=params.user,
            study=study,
            permission_type=StudyPermissionType.RUN,
        )

        self._assert_launcher_is_initialized(launcher)

        self.launchers[launcher].kill_job(job_id=job_id)

        job_status = JobResult(
            id=str(job_id),
            study_id=study_uuid,
            job_status=JobStatus.FAILED,
            launcher=launcher,
        )
        self.job_result_repository.save(job_status)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_JOB_CANCELLED,
                payload=job_status.to_dto().dict(),
                channel=EventChannelDirectory.JOB_STATUS + job_result.id,
            )
        )

        return job_status

    def _filter_from_user_permission(
        self, job_results: List[JobResult], user: Optional[JWTUser]
    ) -> List[JobResult]:
        if not user:
            return []

        allowed_job_results = []
        for job_result in job_results:
            try:
                if assert_permission(
                    user,
                    self.study_service.get_study(job_result.study_id),
                    StudyPermissionType.RUN,
                    raising=False,
                ):
                    allowed_job_results.append(job_result)
            except StudyNotFoundError:
                pass
        return allowed_job_results

    def get_result(
        self, job_uuid: UUID, params: RequestParameters
    ) -> JobResult:
        job_result = self.job_result_repository.get(str(job_uuid))

        try:
            if job_result:
                study = self.study_service.get_study(job_result.study_id)
                assert_permission(
                    user=params.user,
                    study=study,
                    permission_type=StudyPermissionType.READ,
                )
                return job_result

        except StudyNotFoundError:
            pass

        raise JobNotFound()

    def get_jobs(
        self, study_uid: Optional[str], params: RequestParameters
    ) -> List[JobResult]:

        if study_uid is not None:
            job_results = self.job_result_repository.find_by_study(study_uid)
        else:
            job_results = self.job_result_repository.get_all()

        return self._filter_from_user_permission(
            job_results=job_results, user=params.user
        )

    def get_log(
        self, job_id: str, log_type: LogType, params: RequestParameters
    ) -> Optional[str]:
        job_result = self.job_result_repository.get(str(job_id))
        if job_result:
            if job_result.output_id:
                return cast(
                    str,
                    self.study_service.get(
                        job_result.study_id,
                        f"/output/{job_result.output_id}/simulation",
                        depth=1,
                        formatted=True,
                        params=params,
                    ),
                )
            self._assert_launcher_is_initialized(job_result.launcher)
            return self.launchers[job_result.launcher].get_log(
                job_id, log_type
            )
        raise JobNotFound()

    def get_versions(self, params: RequestParameters) -> Dict[str, List[str]]:
        output_dict = {}
        if self.config.launcher.local:
            output_dict["local"] = list(
                self.config.launcher.local.binaries.keys()
            )

        if self.config.launcher.slurm:
            output_dict[
                "slurm"
            ] = self.config.launcher.slurm.antares_versions_on_remote_server

        return output_dict
