import logging
from datetime import datetime
from functools import reduce
from http import HTTPStatus
from pathlib import Path
from typing import List, Optional, cast, Dict
from uuid import UUID, uuid4

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
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import LauncherCallbacks
from antarest.launcher.adapters.factory_launcher import FactoryLauncher
from antarest.launcher.extensions.adequacy_patch.extension import (
    AdequacyPatchExtension,
)
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.launcher.model import (
    JobResult,
    JobStatus,
    LogType,
    JobLog,
    JobLogType,
)
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
                ),
                after_export_flat=lambda job_id, study_id, study_path, launcher_opts: self.after_export_flat_hooks(
                    job_id, study_id, study_path, launcher_opts
                ),
                append_before_log=lambda jobid, message: self.append_log(
                    jobid, message, JobLogType.BEFORE
                ),
                append_after_log=lambda jobid, message: self.append_log(
                    jobid, message, JobLogType.AFTER
                ),
            ),
            event_bus,
        )
        self.extensions = self._init_extensions()

    def _init_extensions(self) -> Dict[str, ILauncherExtension]:
        adequacy_patch_ext = AdequacyPatchExtension(
            self.study_service.storage_service
        )
        return {adequacy_patch_ext.get_name(): adequacy_patch_ext}

    def get_launchers(self) -> List[str]:
        return list(self.launchers.keys())

    def after_export_flat_hooks(
        self,
        job_id: str,
        study_id: str,
        study_exported_path: Path,
        launcher_opts: Optional[JSON],
    ) -> None:
        for ext in self.extensions:
            if (
                launcher_opts is not None
                and launcher_opts.get(ext, None) is not None
            ):
                logger.info(
                    f"Applying extension {ext} after_export_flat_hook on job {job_id}"
                )
                self.extensions[ext].after_export_flat_hook(
                    job_id,
                    study_id,
                    study_exported_path,
                    launcher_opts.get(ext),
                )

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

    def append_log(
        self, job_id: str, message: str, log_type: JobLogType
    ) -> None:
        with db():
            job_result = self.job_result_repository.get(job_id)
            if job_result is not None:
                job_result.logs.append(
                    JobLog(
                        job_id=job_id, message=message, log_type=str(log_type)
                    )
                )
                self.job_result_repository.save(job_result)

    def _assert_launcher_is_initialized(self, launcher: str) -> None:
        if launcher not in self.launchers:
            raise LauncherServiceNotAvailableException(launcher)

    def run_study(
        self,
        study_uuid: str,
        launcher: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> str:
        study_info = self.study_service.get_study_information(
            uuid=study_uuid, params=params
        )
        study_version = study_info.version

        self._assert_launcher_is_initialized(launcher)
        assert_permission(
            user=params.user,
            study=study_info,
            permission_type=StudyPermissionType.RUN,
        )
        job_uuid = str(uuid4())
        job_status = JobResult(
            id=job_uuid,
            study_id=study_uuid,
            job_status=JobStatus.PENDING,
            launcher=launcher,
        )
        self.job_result_repository.save(job_status)

        self.launchers[launcher].run_study(
            study_uuid,
            job_uuid,
            str(study_version),
            launcher_parameters,
            params,
        )

        self.event_bus.push(
            Event(
                type=EventType.STUDY_JOB_STARTED,
                payload=job_status.to_dto().dict(),
                permissions=create_permission_from_study(study_info),
            )
        )
        return job_uuid

    def kill_job(self, job_id: str, params: RequestParameters) -> JobResult:
        logger.info(f"Trying to cancel job {job_id}")
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

    @staticmethod
    def sort_log(
        log: JobLog, logs: Dict[JobLogType, List[str]]
    ) -> Dict[JobLogType, List[str]]:
        logs[
            JobLogType.AFTER
            if log.log_type == JobLogType.AFTER
            else JobLogType.BEFORE
        ].append(log.message)
        return logs

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
            app_logs: Dict[JobLogType, List[str]] = reduce(
                lambda logs, log: LauncherService.sort_log(log, logs),
                job_result.logs,
                {JobLogType.BEFORE: [], JobLogType.AFTER: []},
            )
            launcher_logs = (
                self.launchers[job_result.launcher].get_log(job_id, log_type)
                or ""
            )
            return (
                "\n".join(app_logs[JobLogType.BEFORE])
                + "\n"
                + launcher_logs
                + "\n"
                + "\n".join(app_logs[JobLogType.AFTER])
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
