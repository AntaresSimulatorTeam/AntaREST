import logging
from typing import Any, Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.launcher.model import (
    LogType,
    JobCreationDTO,
    JobResult,
    JobResultDTO,
    LauncherEnginesDTO,
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
        engine: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Launching study {study_id}", extra={"user": current_user.id}
        )
        selected_engine = (
            engine if engine is not None else config.launcher.default
        )

        params = RequestParameters(user=current_user)
        return JobCreationDTO(
            job_id=str(service.run_study(study_id, params, selected_engine))
        )

    @bp.get(
        "/launcher/jobs",
        tags=[APITag.launcher],
        summary="Retrieve jobs",
        response_model=List[JobResultDTO],
    )
    def get_job(
        study: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching execution jobs for study {study or '<all>'}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return [job.to_dto() for job in service.get_jobs(study, params)]

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
        summary="Get list of supported study version for all configures launchers",
        response_model=Dict[str, List[str]],
    )
    def get_versions(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        logger.info(f"Fetching version list")
        return service.get_versions(params=params)

    return bp
