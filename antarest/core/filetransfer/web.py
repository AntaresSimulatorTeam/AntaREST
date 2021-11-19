from pathlib import Path
from typing import Any, List

from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth


def create_file_transfer_api(
    filetransfer_manager: FileTransferManager, config: Config
) -> APIRouter:
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/downloads",
        tags=[APITag.downloads],
        summary="Get available downloads",
        response_model=List[FileDownloadDTO],
    )
    def get_downloads(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        return filetransfer_manager.list_downloads(
            RequestParameters(user=current_user)
        )

    @bp.get(
        "/downloads/{download_id}",
        tags=[APITag.downloads],
        summary="Retrieve download file",
        response_class=FileResponse,
    )
    def fetch_download(
        download_id: str, user: JWTUser = Depends(auth.get_current_user)
    ):
        download = filetransfer_manager.fetch_download(
            download_id, RequestParameters(user=user)
        )
        return FileResponse(
            Path(download.path),
            headers={
                "Content-Disposition": f'attachment; filename="{download.name}"'
            },
            media_type="application/zip",
        )

    return bp
