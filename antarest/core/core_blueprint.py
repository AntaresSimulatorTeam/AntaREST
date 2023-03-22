import logging
from typing import Any

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.web import APITag
from antarest.core.version_info import VersionInfoDTO, get_commit_id
from antarest.login.auth import Auth
from fastapi import APIRouter, Depends
from pydantic import BaseModel


class StatusDTO(BaseModel):
    status: str


def create_utils_routes(config: Config) -> APIRouter:
    """
    Utility endpoints

    Args:
        config: main server configuration
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
        response_model=VersionInfoDTO,
    )
    def version_info() -> Any:
        """
        Returns the current version of the application, along with relevant dependency information.

        - `version`: The current version of the application.
        - `gitcommit`: The commit ID of the current version's Git repository.
        - `dependencies`: A dictionary of dependencies, where the key is
          the dependency name and the value is its version number.
        """
        from antareslauncher import __version__ as antares_launcher_version
        from antarest import __version__ as antarest_version

        return VersionInfoDTO(
            version=antarest_version,
            gitcommit=get_commit_id(config.resources_path),
            dependencies={"Antares_Launcher": antares_launcher_version},
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
