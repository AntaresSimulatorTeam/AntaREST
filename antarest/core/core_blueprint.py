from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.core.version_info import VersionInfoDTO, get_commit_id, get_dependencies
from antarest.login.auth import Auth


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

        - `name`: The name of the application.
        - `version`: The current version of the application.
        - `gitcommit`: The commit ID of the current version's Git repository.
        - `dependencies`: A dictionary of dependencies, where the key is
          the dependency name and the value is its version number.
        """
        from antarest import __version__ as antarest_version

        return VersionInfoDTO(
            version=antarest_version,
            gitcommit=get_commit_id(config.resources_path),
            dependencies=get_dependencies(),
        )

    return bp
