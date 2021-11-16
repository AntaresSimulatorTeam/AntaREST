from typing import Any

from fastapi import APIRouter
from fastapi.params import Depends

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth


def create_file_transfer_api(config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)
    ftm = FileTransferManager.get_instance(config)

    @bp.get(
        "/downloads",
        tags=[APITag.downloads],
        summary="Get available downloads",
        response_model=str,
    )
    def get_downloads(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        return ""

    return bp
