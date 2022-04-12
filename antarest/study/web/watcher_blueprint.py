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
        path: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:

        if path:
            # The front actually sends <workspace>/<path/to/folder>
            try:
                workspace: Optional[str] = path.split("/")[0]
                real_path = Path("/".join(path.split("/")[1:]))
            except:
                raise BadPathFormatError(
                    "Bad path format. Expected <workspace>/<path/to/folder>"
                )
            logger.info(
                f"Scanning directory {real_path}",
                extra={"user": current_user.id},
            )
        else:
            logger.info(
                "Scanning all workspaces",
                extra={"user": current_user.id},
            )
            real_path = None
            workspace = None
        return watcher.oneshot_scan(workspace=workspace, path=real_path)

    return bp
