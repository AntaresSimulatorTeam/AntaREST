import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from antarest import __version__
from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.utils import get_commit_id
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth


class StatusDTO(BaseModel):
    status: str


class VersionDTO(BaseModel):
    version: str
    gitcommit: Optional[str]


def create_utils_routes(config: Config) -> APIRouter:
    """
    Utility endpoints

    Args:
        storage_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter()
    auth = Auth(config)

    @bp.get("/health", tags=[APITag.misc], response_model=StatusDTO)
    def health() -> Any:
        return StatusDTO(status="available")

    @bp.get(
        "/version",
        tags=[APITag.misc],
        summary="Get application version",
        response_model=VersionDTO,
    )
    def version() -> Any:
        return VersionDTO(
            version=__version__, gitcommit=get_commit_id(config.resources_path)
        )

    @bp.get("/kill", include_in_schema=False)
    def kill_worker(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if not current_user.is_site_admin():
            raise UserHasNotPermissionError()
        logging.getLogger(__name__).warning("Killing the worker")
        exit(1)

    return bp
