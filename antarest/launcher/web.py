from typing import Any, Optional
from uuid import UUID

from markupsafe import escape
from fastapi import APIRouter, Depends, Query

from antarest.common.jwt import JWTUser
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.service import LauncherService
from antarest.login.auth import Auth


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    @bp.post(
        "/launcher/run/{study_id}",
        tags=["Run Studies"],
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

    @bp.get("/launcher/jobs", tags=["Run Studies"], summary="Retrieve jobs")
    def get_job(
        study: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        return [job.to_dict() for job in service.get_jobs(study)]

    @bp.get(
        "/launcher/jobs/{job_id}",
        tags=["Run Studies"],
        summary="Retrieve job info from job id",
    )
    def get_result(
        job_id: UUID, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        return service.get_result(job_id).to_dict()

    return bp
