import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.launcher.model import (
    JobCreationDTO,
    JobResultDTO,
    LauncherEnginesDTO,
    LauncherParametersDTO,
    LogType,
)
from antarest.launcher.service import LauncherService
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)

DEFAULT_MAX_LATEST_JOBS = 200


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
                study_id,
                selected_launcher,
                launcher_parameters,
                params,
                version,
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
        latest: Optional[int] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching execution jobs for study {study or '<all>'}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return [
            job.to_dto()
            for job in service.get_jobs(study, params, filter_orphans, latest)
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

    @bp.get(
        "/launcher/jobs/{job_id}/progress",
        tags=[APITag.launcher],
        summary="Retrieve job progress from job id",
        response_model=int,
    )
    def get_progress(
        job_id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(
            f"Fetching job progress of job {job_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return int(service.get_launch_progress(job_id, params))

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
        "/launcher/load",
        tags=[APITag.launcher],
        summary="Get the cluster load in usage percent",
    )
    def get_load(
        from_cluster: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[str, float]:
        params = RequestParameters(user=current_user)
        logger.info("Fetching launcher load")
        return service.get_load(from_cluster)

    @bp.get(
        "/launcher/_versions",
        tags=[APITag.launcher],
        summary="Get list of supported solver versions",
        response_model=List[str],
    )
    def get_solver_versions(
        solver: Optional[str] = Query(
            None,
            examples={
                "default solver": {
                    "description": "Get the solver versions of the default configuration",
                    "value": "",
                },
                "SLURM solver": {
                    "description": "Get the solver versions of the SLURM server if available",
                    "value": "slurm",
                },
                "Local solver": {
                    "description": "Get the solver versions of the Local server if available",
                    "value": "local",
                },
            },
        )
    ) -> List[str]:
        """
        Get list of supported solver versions defined in the configuration.

        Args:
        - `solver`: name of the configuration to read: "default", "slurm" or "local".
        """
        solver = solver or "local"
        logger.info(
            f"Fetching the list of solver versions for the '{solver}' configuration"
        )
        return service.get_solver_versions(solver)

    return bp
