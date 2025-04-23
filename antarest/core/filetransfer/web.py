# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.utils.web import APITag


def create_file_transfer_api(filetransfer_manager: FileTransferManager, config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1")

    @bp.get("/downloads", tags=[APITag.downloads], summary="Get available downloads")
    def get_downloads() -> list[FileDownloadDTO]:
        return filetransfer_manager.list_downloads()

    @bp.get(
        "/downloads/{download_id}",
        tags=[APITag.downloads],
        summary="Retrieve download file",
        response_class=FileResponse,
    )
    def fetch_download(download_id: str) -> Any:
        download = filetransfer_manager.fetch_download(download_id)
        return FileResponse(
            Path(download.path),
            headers={"Content-Disposition": f'attachment; filename="{download.filename}"'},
            media_type="application/zip",
        )

    return bp
