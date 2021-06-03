from typing import Any, Optional
from uuid import UUID

from markupsafe import escape
from fastapi import APIRouter, Depends, Query

from antarest.common.jwt import JWTUser
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.service import LauncherService


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    bp = APIRouter()

    auth = Auth(config)

    @bp.post(
        "/launcher/run/{study_id}", tags=["Run Studies"], summary="Run study"
    )
    def run(
        study_id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        return {"job_id": service.run_study(str(escape(study_id)), params)}

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
