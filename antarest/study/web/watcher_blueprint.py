import logging
from typing import List, Any

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.storage.rawstudy.watcher import Watcher

logger = logging.getLogger(__name__)


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
        "/studies/watcher/scan",
        summary="Launch scan in selected directory",
        tags=[APITag.study_raw_data],
        response_model=List[str],
    )
    def scan_dir(
        path: Optional[str] = None,  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if path:
            logger.info(
                f"Scanning directory {path}",
                extra={"user": current_user.id},
            )
        else:
            logger.info(
                "Scanning all workspaces",
                extra={"user": current_user.id},
            )
        return watcher.oneshot_scan(path)

    return bp
