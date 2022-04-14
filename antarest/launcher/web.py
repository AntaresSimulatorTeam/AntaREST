import logging
from typing import Any, Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.launcher.model import (
    LogType,
    JobCreationDTO,
    JobResultDTO,
    LauncherEnginesDTO,
    LauncherParametersDTO,
)
from antarest.launcher.service import LauncherService
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    @bp.post(
        "/launcher/run/{study_id}",
        tags=[APITag.launcher],
        summary="Run study",
        response_model=JobCreationDTO,
    )
    def run(
        study_id: str,
        launcher: Optional[str] = None,
        launcher_parameters: LauncherParametersDTO = LauncherParametersDTO(),
        version: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Launching study {study_id} with options {launcher_parameters}",
            extra={"user": current_user.id},
        )
        selected_launcher = (
            launcher if launcher is not None else config.launcher.default
        )

        params = RequestParameters(user=current_user)
        return JobCreationDTO(
            job_id=service.run_study(
                study_id, selected_launcher, launcher_parameters, params, version
            )
        )

    @bp.get(
        "/launcher/jobs",
        tags=[APITag.launcher],
        summary="Retrieve jobs",
        response_model=List[JobResultDTO],
    )
    def get_job(
        study: Optional[str] = None,
        filter_orphans: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching execution jobs for study {study or '<all>'}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return [
            job.to_dto()
            for job in service.get_jobs(study, params, filter_orphans)
        ]

    @bp.get(
        "/launcher/jobs/{job_id}/logs",
        tags=[APITag.launcher],
        summary="Retrieve job logs from job id",
    )
    def get_job_log(
        job_id: str,
        log_type: LogType = LogType.STDOUT,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching logs for job {job_id}", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        return service.get_log(job_id, log_type, params)

    @bp.get(
        "/launcher/jobs/{job_id}/output",
        tags=[APITag.launcher],
        summary="Export job output",
        response_model=FileDownloadTaskDTO,
    )
    def export_job_output(
        job_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Exporting output for job {job_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return service.download_output(job_id, params)

    @bp.post(
        "/launcher/jobs/{job_id}/kill",
        tags=[APITag.launcher],
        summary="Kill job",
    )
    def kill_job(
        job_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Killing job {job_id}", extra={"user": current_user.id})

        params = RequestParameters(user=current_user)
        return service.kill_job(
            job_id=job_id,
            params=params,
        ).to_dto()

    @bp.get(
        "/launcher/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Retrieve job info from job id",
        response_model=JobResultDTO,
    )
    def get_result(
        job_id: UUID, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(
            f"Fetching job info {job_id}", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        return service.get_result(job_id, params).to_dto()

    @bp.delete(
        "/launcher/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Remove job",
        response_model=JobResultDTO,
    )
    def remove_result(
        job_id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(f"Removing job {job_id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        service.remove_job(job_id, params)

    @bp.get(
        "/launcher/engines",
        tags=[APITag.launcher],
        summary="Retrieve available engines",
        response_model=LauncherEnginesDTO,
    )
    def get_engines() -> Any:
        logger.info(f"Listing launch engines")
        return LauncherEnginesDTO(engines=service.get_launchers())

    @bp.get(
        "/launcher/_versions",
        tags=[APITag.launcher],
        summary="Get list of supported study version for all configured launchers",
        response_model=Dict[str, List[str]],
    )
    def get_versions(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        logger.info(f"Fetching version list")
        return service.get_versions(params=params)

    return bp
