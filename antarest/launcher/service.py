# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import functools
import logging
import os
import shutil
from http import HTTPStatus
from pathlib import Path
from uuid import UUID, uuid4

from antares.study.version import SolverVersion
from fastapi import HTTPException

from antarest.core.config import Config, InvalidConfigurationError
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType, IEventBus
from antarest.core.model import PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService
from antarest.core.utils.archives import ArchiveFormat, archive_dir, is_zip, read_in_zip
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch, current_time
from antarest.launcher.adapters.abstractlauncher import LauncherCallbacks, SimulationLogs
from antarest.launcher.adapters.factory_launcher import FactoryLauncher
from antarest.launcher.exceptions import NoValidOutputError
from antarest.launcher.extensions.adequacy_patch.extension import AdequacyPatchExtension
from antarest.launcher.extensions.interface import ILauncherExtension
from antarest.launcher.model import (
    JobLog,
    JobLogType,
    JobResult,
    JobStatus,
    LauncherInfoDTO,
    LauncherListDTO,
    LauncherLoadDTO,
    LauncherParametersDTO,
    LauncherResourceRangeDTO,
    LogType,
    SolverPresets,
    SolverPresetsCreation,
    SolverPresetsDB,
    SolverPresetsUpdate,
    XpansionParametersDTO,
    apply_update_solver_presets,
    is_version_covered_by_config,
)
from antarest.launcher.repository import JobResultRepository, SolverPresetsRepository
from antarest.login.service import LoginService
from antarest.login.utils import current_user_context, get_current_user, require_current_user
from antarest.output.service import OutputService
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from antarest.study.storage.utils import assert_permission, extract_output_name, find_single_output_path

logger = logging.getLogger(__name__)


class JobNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.NOT_FOUND)


class IncompatibleSolverPresets(HTTPException):
    def __init__(self, message: str = "Invalid solver presets"):
        super().__init__(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=message,
        )


class SolverPresetsNotFound(HTTPException):
    def __init__(self, message: str = "Solver presets not found"):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            detail=message,
        )


class LauncherServiceNotAvailableException(HTTPException):
    def __init__(self, engine: str):
        super().__init__(HTTPStatus.BAD_REQUEST, f"The engine {engine} is not available")


LAUNCHER_PARAM_NAME_SUFFIX = "output_suffix"
EXECUTION_INFO_FILE = "execution_info.ini"


class LauncherService:
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        output_service: OutputService,
        login_service: LoginService,
        job_result_repository: JobResultRepository,
        solver_presets_repository: SolverPresetsRepository,
        event_bus: IEventBus,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        cache: ICache,
        factory_launcher: FactoryLauncher = FactoryLauncher(),
    ) -> None:
        self.config = config
        self.study_service = study_service
        self.output_service = output_service
        self.login_service = login_service
        self.job_result_repository = job_result_repository
        self.solver_presets_repository = solver_presets_repository
        self.event_bus = event_bus
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.launchers = factory_launcher.build_launcher(
            config,
            LauncherCallbacks(
                update_status=self.update,
                export_study=self._export_study,
                append_before_log=lambda jobid, message: self.append_log(jobid, message, JobLogType.BEFORE),
                append_after_log=lambda jobid, message: self.append_log(jobid, message, JobLogType.AFTER),
                import_output=self._import_output,
            ),
            event_bus,
            cache,
        )
        self.extensions = self._init_extensions()

    def _init_extensions(self) -> dict[str, ILauncherExtension]:
        adequacy_patch_ext = AdequacyPatchExtension(self.study_service, self.config)
        return {adequacy_patch_ext.get_name(): adequacy_patch_ext}

    def get_launchers(self) -> LauncherListDTO:
        configs = self.config.launcher.configs or []
        launchers: list[LauncherInfoDTO] = []
        for launcher_config in configs:
            launchers.append(
                LauncherInfoDTO(
                    id=launcher_config.id,
                    name=launcher_config.name,
                    nb_cores=LauncherResourceRangeDTO(
                        min=launcher_config.nb_cores.min,
                        max=launcher_config.nb_cores.max,
                        default=launcher_config.nb_cores.default,
                    ),
                    time_limit=LauncherResourceRangeDTO(
                        min=launcher_config.time_limit.min,
                        max=launcher_config.time_limit.max,
                        default=launcher_config.time_limit.default,
                    ),
                    versions=self.get_solver_versions(launcher_config.id),
                )
            )
        default_launcher = self.config.launcher.default
        return LauncherListDTO(launchers=launchers, default_launcher=default_launcher)

    def _after_export_flat_hooks(
        self,
        job_id: str,
        study_id: str,
        study_exported_path: Path,
        launcher_params: LauncherParametersDTO,
    ) -> None:
        for ext in self.extensions:
            if launcher_params is not None and launcher_params.__getattribute__(ext) is not None:
                logger.info(f"Applying extension {ext} after_export_flat_hook on job {job_id}")
                with db():
                    self.extensions[ext].after_export_flat_hook(
                        job_id,
                        study_id,
                        study_exported_path,
                        launcher_params.__getattribute__(ext),
                    )

    def update(
        self,
        job_uuid: str,
        status: JobStatus,
        msg: str | None,
        output_id: str | None,
    ) -> None:
        with db():
            logger.info(f"Setting study with job id {job_uuid} status to {status}")
            job_result = self.job_result_repository.get(job_uuid)
            if job_result is not None:
                job_result.job_status = status
                job_result.msg = msg
                job_result.output_id = output_id
                final_status = status in [JobStatus.SUCCESS, JobStatus.FAILED]
                if final_status:
                    job_result.completion_date = current_time()
                self.job_result_repository.save(job_result)
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_JOB_COMPLETED if final_status else EventType.STUDY_JOB_STATUS_UPDATE,
                        payload=job_result.to_dto().model_dump(mode="json"),
                        permissions=PermissionInfo(public_mode=PublicMode.READ),
                        channel=EventChannelDirectory.JOB_STATUS + job_result.id,
                    )
                )
            logger.info("Study status set")

    def append_log(self, job_id: str, message: str, log_type: JobLogType) -> None:
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
        launcher_parameters: LauncherParametersDTO,
        solver_presets_id: str | None = None,
        version: str | None = None,
    ) -> str:
        job_uuid = self._generate_new_id()
        logger.info(f"New study launch (study={study_uuid}, job_id={job_uuid})")
        study_info = self.study_service.get_study_information(uuid=study_uuid)
        solver_version = SolverVersion.parse(version or study_info.version)

        if solver_presets_id is not None:
            solver_presets = self.get_solver_presets(solver_presets_id)
            if not is_version_covered_by_config(solver_presets, solver_version):
                raise IncompatibleSolverPresets("Solver presets are not compatible with study version")
            if launcher_parameters.other_options:
                raise IncompatibleSolverPresets("Cannot use other_options when solver presets are specified")
            launcher_parameters.other_options = solver_presets.to_cli_options()

        self._assert_launcher_is_initialized(launcher)
        assert_permission(
            study=study_info,
            permission_type=StudyPermissionType.RUN,
        )
        owner_id: int = 0
        if user := get_current_user():
            owner_id = user.impersonator if user.type == "bots" else user.id
        job_status = JobResult(
            id=job_uuid,
            study_id=study_uuid,
            job_status=JobStatus.PENDING,
            launcher=launcher,
            launcher_params=launcher_parameters.model_dump_json() if launcher_parameters else None,
            owner_id=(owner_id or None),
        )
        self.job_result_repository.save(job_status)

        self.launchers[launcher].run_study(study_uuid, job_uuid, solver_version, launcher_parameters)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_JOB_STARTED,
                payload=job_status.to_dto().model_dump(),
                permissions=PermissionInfo.from_study(study_info),
            )
        )
        return job_uuid

    def kill_job(self, job_id: str) -> JobResult:
        logger.info(f"Trying to cancel job {job_id}")
        job_result = self.job_result_repository.get(job_id)
        if job_result is None:
            raise ValueError(f"Job {job_id} not found")

        study_uuid = job_result.study_id
        study = self.study_service.get_study(study_uuid)
        assert_permission(
            study=study,
            permission_type=StudyPermissionType.RUN,
        )

        launcher = job_result.launcher
        if launcher is None:
            raise ValueError(f"Job {job_id} has no launcher")
        self._assert_launcher_is_initialized(launcher)

        self.launchers[launcher].kill_job(job_id=job_id)

        owner_id = 0
        if user := get_current_user():
            owner_id = user.impersonator if user.type == "bots" else user.id
        job_status = JobResult(
            id=str(job_id),
            study_id=study_uuid,
            job_status=JobStatus.FAILED,
            launcher=launcher,
            owner_id=(owner_id or None),
        )
        self.job_result_repository.save(job_status)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_JOB_CANCELLED,
                payload=job_status.to_dto().model_dump(),
                permissions=PermissionInfo.from_study(study),
                channel=EventChannelDirectory.JOB_STATUS + job_result.id,
            )
        )

        return job_status

    def _filter_from_user_permission(self, job_results: list[JobResult]) -> list[JobResult]:
        user = get_current_user()
        if not user:
            return []

        allowed_job_results = []

        study_ids = [job_result.study_id for job_result in job_results]
        if study_ids:
            studies = {
                study.id: study
                for study in self.study_service.repository.get_all(
                    study_filter=StudyFilter(study_ids=study_ids, access_permissions=AccessPermissions.for_user(user))
                )
            }
        else:
            studies = {}

        for job_result in job_results:
            if job_result.study_id in studies:
                try:
                    assert_permission(studies[job_result.study_id], StudyPermissionType.RUN)
                except UserHasNotPermissionError:
                    continue
                else:
                    allowed_job_results.append(job_result)
            elif user and (user.is_site_admin() or user.is_admin_token()):
                allowed_job_results.append(job_result)
        return allowed_job_results

    def get_result(self, job_uuid: UUID) -> JobResult:
        job_result = self.job_result_repository.get(str(job_uuid))

        try:
            if job_result:
                study = self.study_service.get_study(job_result.study_id)
                assert_permission(
                    study=study,
                    permission_type=StudyPermissionType.READ,
                )
                return job_result

        except StudyNotFoundError:
            pass

        raise JobNotFound()

    def remove_job(self, job_id: str) -> None:
        user = get_current_user()
        if user and user.is_site_admin():
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
        study_uid: str | None,
        filter_orphans: bool = True,
        latest: int | None = None,
    ) -> list[JobResult]:
        if study_uid is not None:
            job_results = self.job_result_repository.find_by_study(study_uid)
        else:
            job_results = self.job_result_repository.get_all(filter_orphan=filter_orphans, latest=latest)

        return self._filter_from_user_permission(job_results=job_results)

    @staticmethod
    def sort_log(log: JobLog, logs: dict[JobLogType, list[str]]) -> dict[JobLogType, list[str]]:
        logs[JobLogType.AFTER if log.log_type == str(JobLogType.AFTER) else JobLogType.BEFORE].append(log.message)
        return logs

    def get_log(self, job_id: str, log_type: LogType) -> str:
        job_result = self.job_result_repository.get(str(job_id))
        if not job_result:
            raise JobNotFound()

        launcher_logs: str
        if job_result.output_id:
            launcher_logs = self.output_service.get_logs(job_result.study_id, job_result.output_id, log_type)
        else:
            if job_result.launcher is None:
                raise ValueError(f"Job {job_id} has no launcher")
            self._assert_launcher_is_initialized(job_result.launcher)
            launcher_logs = self.launchers[job_result.launcher].get_log(job_id, log_type) or ""
        if log_type == LogType.STDOUT:
            app_logs: dict[JobLogType, list[str]] = functools.reduce(
                lambda logs, log: LauncherService.sort_log(log, logs),
                job_result.logs or [],
                {JobLogType.BEFORE: [], JobLogType.AFTER: []},
            )
            return "\n".join(app_logs[JobLogType.BEFORE] + [launcher_logs] + app_logs[JobLogType.AFTER])
        return launcher_logs

    def _export_study(
        self,
        job_id: str,
        study_id: str,
        target_path: Path,
        launcher_params: LauncherParametersDTO,
    ) -> None:
        self.append_log(job_id, f"Extracting study {study_id}", JobLogType.BEFORE)
        with db():
            output_list = (
                [launcher_params.xpansion.output_id]
                if launcher_params.xpansion
                and isinstance(launcher_params.xpansion, XpansionParametersDTO)
                and launcher_params.xpansion.output_id is not None
                else None
            )
            self.study_service.export_study_flat(
                study_id,
                target_path,
                output_list=output_list,
            )
        self.append_log(job_id, "Study extracted", JobLogType.BEFORE)
        self._after_export_flat_hooks(job_id, study_id, target_path, launcher_params)

    def _get_job_output_fallback_path(self, job_id: str) -> Path:
        return self.config.storage.tmp_dir / f"output_{job_id}"

    def _import_fallback_output(
        self,
        job_id: str,
        output_path: Path,
        output_suffix_name: str | None = None,
    ) -> str | None:
        # Temporary import the output in a tmp space if the study can not be found
        logger.info(f"Trying to import output in fallback tmp space for job {job_id}")
        output_name: str | None = None
        job_output_path = self._get_job_output_fallback_path(job_id)

        try:
            output_name = extract_output_name(output_path, output_suffix_name)
            os.mkdir(job_output_path)
            if output_path.suffix != ".zip":
                imported_output_path = job_output_path / "imported"
                shutil.copytree(output_path, imported_output_path)
                imported_output_path.rename(Path(job_output_path, output_name))
            else:
                shutil.copy(output_path, job_output_path / f"{output_name}.zip")

        except Exception as e:
            logger.error("Failed to import output in fallback mode", exc_info=e)
            shutil.rmtree(job_output_path, ignore_errors=True)
        return output_name

    def _save_solver_stats_file(self, job_result: JobResult, measurement_file: Path | None) -> None:
        if measurement_file and measurement_file.exists():
            job_result.solver_stats = measurement_file.read_text(encoding="utf-8")
            self.job_result_repository.save(job_result)

    def _save_solver_stats(self, job_result: JobResult, output_path: Path) -> None:
        try:
            if is_zip(output_path):
                read_in_zip(
                    output_path,
                    Path(EXECUTION_INFO_FILE),
                    lambda stat_file: self._save_solver_stats_file(job_result, stat_file),
                )
            else:
                self._save_solver_stats_file(job_result, output_path / EXECUTION_INFO_FILE)
        except Exception as e:
            logger.error("Failed to save solver performance measurements", exc_info=e)

    def _import_output(
        self,
        job_id: str,
        output_path: Path,
        additional_logs: SimulationLogs,
    ) -> str | None:
        """
        In the current state (2026-03-04), we actually always get a parent directory of the output here.
        We never get a zip. Zip support was partially added in the past when planning to get an output
        zip directly from antares-launcher, but it was never completed.

        TODO: we should clarify this whole workflow, including the "optimized path" for studies stored
              on external devices, see comment below.
        """
        logger.info(f"Importing output for job {job_id}")
        with db():
            job_result = self.job_result_repository.get(job_id)
            if not job_result:
                raise JobNotFound()
            study_id = job_result.study_id
            job_owner_id = job_result.owner_id
            job_launch_params = LauncherParametersDTO.from_launcher_params(job_result.launcher_params)

            output_true_path = find_single_output_path(output_path)

            if not output_true_path.is_dir() and not is_zip(output_true_path):
                raise NoValidOutputError(f"No valid output for job {job_id}: {output_true_path}")

            self._save_solver_stats(job_result, output_true_path)

        zip_path: Path | None = None
        # Optimized path for studies stored on external devices, that will then be unarchived there.
        # TODO: that whole optimization path should be refactored to:
        #       - be more explicit
        #       - not affect internal studies
        if job_launch_params.archive_output:
            stopwatch = StopWatch()
            logger.info("Re zipping output for transfer")
            zip_path = output_true_path.parent / f"{output_true_path.name}.zip"
            archive_dir(output_true_path, target_archive_path=zip_path, archive_format=ArchiveFormat.ZIP)
            logger.info(f"Zipped output for job {job_id} in {stopwatch}s")
            final_output_path = zip_path
        else:
            final_output_path = output_true_path

        with db():
            try:
                if job_owner_id:
                    # We restore the user context as the following processes need it
                    current_user = self.login_service.get_jwt(job_owner_id)
                else:
                    current_user = get_current_user()

                with current_user_context(current_user):
                    return self.output_service.import_output(
                        study_id,
                        final_output_path,
                        output_name_suffix=job_launch_params.output_suffix,
                        auto_unzip=job_launch_params.auto_unzip,
                        logs=additional_logs,
                    )
            except StudyNotFoundError:
                return self._import_fallback_output(
                    job_id,
                    final_output_path,
                    job_launch_params.output_suffix,
                )
            finally:
                # Delete the temporary zip file, which now has been imported
                if zip_path:
                    os.unlink(zip_path)

    def _download_fallback_output(self, job_id: str) -> FileDownloadTaskDTO:
        output_path = self._get_job_output_fallback_path(job_id)
        if output_path.exists():
            logger.info(f"Exporting {job_id} fallback output")
            export_name = f"Job output {output_path.name} export"
            export_file_download = self.file_transfer_manager.request_download(f"{job_id}.zip", export_name)
            export_path = Path(export_file_download.path)
            export_id = export_file_download.id

            def export_task(_: ITaskNotifier) -> TaskResult:
                try:
                    #
                    archive_dir(output_path, export_path, archive_format=ArchiveFormat.ZIP)
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
                progress=None,
                custom_event_messages=None,
            )

            return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

        raise FileNotFoundError()

    def download_output(self, job_id: str) -> FileDownloadTaskDTO:
        logger.info(f"Downloading output for job {job_id}")
        job_result = self.job_result_repository.get(job_id)
        if job_result and job_result.output_id:
            if self._get_job_output_fallback_path(job_id).exists():
                return self._download_fallback_output(job_id)
            self.study_service.get_study(job_result.study_id)
            return self.output_service.export_output(job_result.study_id, job_result.output_id)
        raise JobNotFound()

    def get_load(self, launcher_id: str | None) -> LauncherLoadDTO:
        """
        Get the load of the specified launcher.
        """
        if launcher_id is None:
            launcher_id = self.config.launcher.default

        launcher = self.launchers.get(launcher_id)
        if launcher is None:
            raise InvalidConfigurationError(launcher_id)

        return launcher.get_load()

    def get_solver_versions(self, launcher_id: str | None) -> list[SolverVersion]:
        """
        Fetch the list of solver versions from the configuration.

        Args:
            launcher_id: id of the configuration to read.

        Returns:
            The list of solver versions.
            This list is empty if the configuration is not available.

        Raises:
            InvalidConfigurationError: if the launcher doesn't exist in the configuration.
        """
        if launcher_id is None:
            launcher_id = self.config.launcher.default

        launcher = self.launchers.get(launcher_id)
        if launcher is None:
            raise InvalidConfigurationError(launcher_id)

        return launcher.get_solver_versions()

    def get_launch_progress(self, job_id: str) -> float:
        job_result = self.job_result_repository.get(job_id)
        if not job_result:
            raise JobNotFound()
        study_uuid = job_result.study_id
        launcher = job_result.launcher
        study = self.study_service.get_study(study_uuid)
        assert_permission(
            study=study,
            permission_type=StudyPermissionType.READ,
        )

        if launcher is None:
            raise ValueError(f"Job {job_id} has no launcher")
        launch_progress_json = self.launchers[launcher].cache.get(id=f"Launch_Progress_{job_id}") or {"progress": 0.0}
        return float(launch_progress_json.get("progress", 0.0))

    def create_solver_presets(self, solver_presets_creation: SolverPresetsCreation) -> SolverPresets:
        """
        Create a new solver presets.
        """
        solver_presets_id = str(uuid4())
        solver_presets = SolverPresets.model_validate(
            {**solver_presets_creation.model_dump(exclude_unset=True), "id": solver_presets_id}
        )
        solver_presets_db = SolverPresetsDB.from_model(solver_presets)
        created_solver_presets_db = self.solver_presets_repository.save(solver_presets_db)
        return created_solver_presets_db.to_model()

    def get_solver_presets(self, solver_presets_id: str) -> SolverPresets:
        """
        Retrieve a solver presets configuration by its ID.
        """
        solver_presets_db = self.solver_presets_repository.get(solver_presets_id)
        if not solver_presets_db:
            raise SolverPresetsNotFound(f"Solver presets configuration with id '{solver_presets_id}' not found.")
        return solver_presets_db.to_model()

    def get_solver_presets_list(self) -> list[SolverPresets]:
        """
        Retrieve all solver presets.
        """
        configs = self.solver_presets_repository.get_all()
        return [config.to_model() for config in configs]

    def update_solver_presets(self, configuration_id: str, solver_presets_update: SolverPresetsUpdate) -> SolverPresets:
        """
        Update an existing solver presets using SolverPresetsUpdate.
        """
        user = require_current_user()
        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        solver_presets_db = self.solver_presets_repository.get(configuration_id)
        if not solver_presets_db:
            raise SolverPresetsNotFound(configuration_id)
        # Update only the fields that are provided in the update DTO
        updated_solver_presets = apply_update_solver_presets(solver_presets_db, solver_presets_update)
        updated_solver_presets_db = self.solver_presets_repository.save(updated_solver_presets)
        return updated_solver_presets_db.to_model()

    def delete_solver_presets(self, solver_presets_id: str) -> None:
        """
        Delete a solver presets by its ID. Only site administrators can delete configs.
        """
        user = require_current_user()
        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        solver_presets_db = self.solver_presets_repository.get(solver_presets_id)
        if not solver_presets_db:
            raise SolverPresetsNotFound(solver_presets_id)

        logger.info(f"Deleting solver presets {solver_presets_id}")
        self.solver_presets_repository.delete(solver_presets_id)
