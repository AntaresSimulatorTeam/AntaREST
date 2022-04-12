import logging
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path
from typing import List, Any, Optional

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.storage.rawstudy.watcher import Watcher

logger = logging.getLogger(__name__)


class BadPathFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


def create_watcher_routes(
    watcher: Watcher,
    config: Config,
) -> APIRouter:
    """
    Endpoint implementation for watcher management
    Args:
        watcher: watcher service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.post(
        "/watcher/_scan",
        summary="Launch scan in selected directory",
        tags=[APITag.study_raw_data],
        response_model=List[str],
    )
    def scan_dir(
        path: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:

        if path:
            # The front actually sends <workspace>/<path/to/folder>
            try:
                path_components: List[str] = path.strip("/").split("/")
                workspace = path_components[0]
                relative_path = "/".join(path_components[1:])
            except Exception as e:
                logger.error(
                    "Unexpected exception when tying to retrieve scan path components",
                    exc_info=e,
                )
                raise BadPathFormatError(
                    "Bad path format. Expected <workspace>/<path/to/folder>"
                )
            logger.info(
                f"Scanning directory {relative_path} of worskpace {workspace}",
                extra={"user": current_user.id},
            )
        else:
            logger.info(
                "Scanning all workspaces",
                extra={"user": current_user.id},
            )
            relative_path = None
            workspace = None
        return watcher.oneshot_scan(workspace=workspace, path=relative_path)

    return bp
