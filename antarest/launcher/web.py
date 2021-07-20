from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.launcher.model import LogType
from antarest.launcher.service import LauncherService
from antarest.login.auth import Auth


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    @bp.post(
        "/launcher/run/{study_id}",
        tags=[APITag.launcher],
        summary="Run study",
    )
    def run(
        study_id: str,
        engine: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        """
        Run study
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                    $ref: '#/definitions/RunInfo'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        parameters:
        - in: path
          name: study_id
          required: true
          description: study id
          schema:
            type: string
        definitions:
            - schema:
                id: RunInfo
                properties:
                  job_id:
                    type: string
        tags:
          - Run Studies
        """

        selected_engine = (
            engine if engine is not None else config.launcher.default
        )

        params = RequestParameters(user=current_user)
        return {"job_id": service.run_study(study_id, params, selected_engine)}

    @bp.get("/launcher/jobs", tags=[APITag.launcher], summary="Retrieve jobs")
    def get_job(
        study: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        return [job.to_dict() for job in service.get_jobs(study, params)]

    @bp.get(
        "/launcher/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Retrieve job info from job id",
    )
    def get_result(
        job_id: UUID, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        return service.get_result(job_id, params).to_dict()

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
        params = RequestParameters(user=current_user)
        return service.get_log(job_id, log_type, params)

    @bp.get(
        "/launcher/engines",
        tags=[APITag.launcher],
        summary="Retrieve available engines",
    )
    def get_engines() -> Any:
        return {"engines": service.get_launchers()}

    return bp
