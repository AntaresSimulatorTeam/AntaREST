import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from functools import reduce
from http import HTTPStatus
from pathlib import Path
from typing import List, Optional, cast, Dict
from uuid import UUID, uuid4

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
    EventChannelDirectory,
)
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.core.tasks.service import TaskUpdateNotifier, ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
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
from antarest.study.model import ExportFormat
from antarest.study.service import StudyService
from antarest.core.model import (
    StudyPermissionType,
    PermissionInfo,
    JSON,
)
from antarest.study.storage.utils import (
    assert_permission,
    create_permission_from_study,
    extract_output_name,
    fix_study_root,
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


ORPHAN_JOBS_VISIBILITY_THRESHOLD = 10  # days


class LauncherService:
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        job_result_repository: JobResultRepository,
        event_bus: IEventBus,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        factory_launcher: FactoryLauncher = FactoryLauncher(),
    ) -> None:
        self.config = config
        self.study_service = study_service
        self.job_result_repository = job_result_repository
        self.event_bus = event_bus
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.launchers = factory_launcher.build_launcher(
            config,
            LauncherCallbacks(
                update_status=self.update,
                export_study=self._export_study,
                append_before_log=lambda jobid, message: self.append_log(
                    jobid, message, JobLogType.BEFORE
                ),
                append_after_log=lambda jobid, message: self.append_log(
                    jobid, message, JobLogType.AFTER
                ),
                import_output=self._import_output,
            ),
            event_bus,
            study_service.storage_service.raw_study_service.study_factory,
        )
        self.extensions = self._init_extensions()

    def _init_extensions(self) -> Dict[str, ILauncherExtension]:
        adequacy_patch_ext = AdequacyPatchExtension(
            self.study_service, self.config
        )
        return {adequacy_patch_ext.get_name(): adequacy_patch_ext}

    def get_launchers(self) -> List[str]:
        return list(self.launchers.keys())

    def _after_export_flat_hooks(
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

    def _before_import_hooks(
        self,
        job_id: str,
        study_id: str,
        study_output_path: Path,
        launcher_opts: Optional[JSON],
    ) -> None:
        for ext in self.extensions:
            if (
                launcher_opts is not None
                and launcher_opts.get(ext, None) is not None
            ):
                logger.info(
                    f"Applying extension {ext} before_import_hook on job {job_id}"
                )
                self.extensions[ext].before_import_hook(
                    job_id,
                    study_id,
                    study_output_path,
                    launcher_opts.get(ext),
                )

    def update(
        self,
        job_uuid: str,
        status: JobStatus,
        msg: Optional[str],
        output_id: Optional[str],
    ) -> None:
        with db():
            logger.info(
                f"Setting study with job id {job_uuid} status to {status}"
            )
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
                        channel=EventChannelDirectory.JOB_STATUS
                        + job_result.id,
                    )
                )
            logger.info(f"Study status set")

    def append_log(
        self, job_id: str, message: str, log_type: JobLogType
    ) -> None:
        try:
            with db():
                job_result = self.job_result_repository.get(job_id)
                if job_result is not None:
                    job_result.logs.append(
                        JobLog(
                            job_id=job_id,
                            message=message,
                            log_type=str(log_type),
                        )
                    )
                    self.job_result_repository.save(job_result)
        except Exception as e:
            logger.error(
                f"Failed to append log with message {message} to job {job_id}",
                exc_info=e,
            )

    def _assert_launcher_is_initialized(self, launcher: str) -> None:
        if launcher not in self.launchers:
            raise LauncherServiceNotAvailableException(launcher)

    @staticmethod
    def _generate_new_id() -> str:
        return str(uuid4())

    def run_study(
        self,
        study_uuid: str,
        launcher: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> str:
        job_uuid = self._generate_new_id()
        logger.info(
            f"New study launch (study={study_uuid}, job_id={job_uuid})"
        )
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
        job_status = JobResult(
            id=job_uuid,
            study_id=study_uuid,
            job_status=JobStatus.PENDING,
            launcher=launcher,
            launcher_params=json.dumps(launcher_parameters)
            if launcher_parameters
            else None,
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

        orphan_visibility_threshold = datetime.utcnow() - timedelta(
            days=ORPHAN_JOBS_VISIBILITY_THRESHOLD
        )
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
                if (
                    (user and user.is_site_admin())
                    or job_result.creation_date >= orphan_visibility_threshold
                ):
                    allowed_job_results.append(job_result)
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

    def remove_job(self, job_id: str, params: RequestParameters) -> None:
        if params.user and params.user.is_site_admin():
            logger.info(f"Deleting job {job_id}")
            job_output = self._get_job_output_fallback_path(job_id)
            if job_output.exists():
                logger.info(f"Deleting job output {job_id}")
                shutil.rmtree(job_output, ignore_errors=True)
            self.job_result_repository.delete(job_id)
            return
        raise UserHasNotPermissionError()

    def get_jobs(
        self,
        study_uid: Optional[str],
        params: RequestParameters,
        filter_orphans: bool = True,
    ) -> List[JobResult]:

        if study_uid is not None:
            job_results = self.job_result_repository.find_by_study(study_uid)
        else:
            job_results = self.job_result_repository.get_all(
                filter_orphan=filter_orphans
            )

        return self._filter_from_user_permission(
            job_results=job_results, user=params.user
        )

    @staticmethod
    def sort_log(
        log: JobLog, logs: Dict[JobLogType, List[str]]
    ) -> Dict[JobLogType, List[str]]:
        logs[
            JobLogType.AFTER
            if log.log_type == str(JobLogType.AFTER)
            else JobLogType.BEFORE
        ].append(log.message)
        return logs

    def get_log(
        self, job_id: str, log_type: LogType, params: RequestParameters
    ) -> Optional[str]:
        job_result = self.job_result_repository.get(str(job_id))
        if job_result:
            if job_result.output_id:
                if log_type == LogType.STDOUT:
                    launcher_logs = cast(
                        bytes,
                        self.study_service.get(
                            job_result.study_id,
                            f"/output/{job_result.output_id}/antares-out",
                            depth=1,
                            formatted=True,
                            params=params,
                        )
                        or self.study_service.get(
                            job_result.study_id,
                            f"/output/{job_result.output_id}/simulation",
                            depth=1,
                            formatted=True,
                            params=params,
                        ),
                    ).decode("utf-8")
                else:
                    launcher_logs = cast(
                        bytes,
                        self.study_service.get(
                            job_result.study_id,
                            f"/output/{job_result.output_id}/antares-err",
                            depth=1,
                            formatted=True,
                            params=params,
                        ),
                    ).decode("utf-8")
            else:
                self._assert_launcher_is_initialized(job_result.launcher)
                launcher_logs = str(
                    self.launchers[job_result.launcher].get_log(
                        job_id, log_type
                    )
                    or ""
                )
            if log_type == LogType.STDOUT:
                app_logs: Dict[JobLogType, List[str]] = reduce(
                    lambda logs, log: LauncherService.sort_log(log, logs),
                    job_result.logs or [],
                    {JobLogType.BEFORE: [], JobLogType.AFTER: []},
                )
                return "\n".join(
                    app_logs[JobLogType.BEFORE]
                    + [launcher_logs]
                    + app_logs[JobLogType.AFTER]
                )
            return launcher_logs

        raise JobNotFound()

    def _export_study(
        self,
        job_id: str,
        study_id: str,
        target_path: Path,
        launcher_params: Optional[JSON],
    ) -> None:
        with db():
            self.append_log(
                job_id, f"Extracting study {study_id}", JobLogType.BEFORE
            )
            self.study_service.export_study_flat(
                study_id,
                RequestParameters(DEFAULT_ADMIN_USER),
                target_path,
                outputs=False,
            )
            self.append_log(job_id, "Study extracted", JobLogType.BEFORE)
            self._after_export_flat_hooks(
                job_id, study_id, target_path, launcher_params
            )

    def _get_job_output_fallback_path(self, job_id: str) -> Path:
        return self.config.storage.tmp_dir / f"output_{job_id}"

    def _import_fallback_output(
        self,
        job_id: str,
        output_path: Path,
        additional_logs: Dict[str, List[Path]],
    ) -> Optional[str]:
        logger.info(
            f"Trying to import output in fallback tmp space for job {job_id}"
        )
        output_name: Optional[str] = None
        job_output_path = self._get_job_output_fallback_path(job_id)
        try:
            os.mkdir(job_output_path)
            imported_output = job_output_path / "imported"
            shutil.copytree(output_path, imported_output)
            fix_study_root(imported_output)
            output_name = extract_output_name(imported_output)
            imported_output.rename(Path(job_output_path, output_name))
            if additional_logs:
                for log_name, log_paths in additional_logs.items():
                    with open(
                        Path(job_output_path, output_name) / log_name, "w"
                    ) as fh:
                        for log_path in log_paths:
                            with open(log_path, "r") as infile:
                                for line in infile:
                                    fh.write(line)
        except Exception as e:
            logger.error(
                "Failed to import output in fallback mode", exc_info=e
            )
            shutil.rmtree(job_output_path, ignore_errors=True)
        return output_name

    def _import_output(
        self,
        job_id: str,
        output_path: Path,
        additional_logs: Dict[str, List[Path]],
    ) -> Optional[str]:
        logger.info(f"Importing output for job {job_id}")
        with db():
            job_result = self.job_result_repository.get(job_id)
            if job_result:
                # todo find output_path true root
                self._before_import_hooks(
                    job_id,
                    job_result.study_id,
                    output_path,
                    json.loads(job_result.launcher_params)
                    if job_result.launcher_params
                    else None,
                )
                try:
                    return self.study_service.import_output(
                        job_result.study_id,
                        output_path,
                        RequestParameters(DEFAULT_ADMIN_USER),
                        additional_logs,
                    )
                except StudyNotFoundError:
                    return self._import_fallback_output(
                        job_id, output_path, additional_logs
                    )
        raise JobNotFound()

    def _download_fallback_output(
        self, job_id: str, params: RequestParameters
    ) -> FileDownloadTaskDTO:
        output_path = self._get_job_output_fallback_path(job_id)
        if output_path.exists():
            logger.info(f"Exporting {job_id} fallback output")
            export_name = f"Job output {output_path.name} export"
            export_file_download = self.file_transfer_manager.request_download(
                f"{job_id}.zip",
                export_name,
                params.user,
            )
            export_path = Path(export_file_download.path)
            export_id = export_file_download.id

            def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
                try:
                    shutil.make_archive(
                        base_name=os.path.splitext(export_path)[0],
                        format="zip",
                        root_dir=output_path,
                    )
                    self.file_transfer_manager.set_ready(export_id)
                    return TaskResult(success=True, message="")
                except Exception as e:
                    self.file_transfer_manager.fail(export_id, str(e))
                    raise e

            task_id = self.task_service.add_task(
                export_task,
                export_name,
                task_type=TaskType.EXPORT,
                ref_id=None,
                custom_event_messages=None,
                request_params=params,
            )

            return FileDownloadTaskDTO(
                file=export_file_download.to_dto(), task=task_id
            )

        raise FileNotFoundError()

    def download_output(
        self, job_id: str, params: RequestParameters
    ) -> FileDownloadTaskDTO:
        logger.info(f"Downloading output for job {job_id}")
        job_result = self.job_result_repository.get(job_id)
        if job_result and job_result.output_id:
            if self._get_job_output_fallback_path(job_id).exists():
                return self._download_fallback_output(job_id, params)
            self.study_service.get_study(job_result.study_id)
            return self.study_service.export_output(
                job_result.study_id,
                job_result.output_id,
                params,
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
