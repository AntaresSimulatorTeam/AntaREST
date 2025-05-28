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
from antarest.core.filetransfer.model import FileDownloadDTO, FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth


def create_file_transfer_api(filetransfer_manager: FileTransferManager, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

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

    @bp.get(
        "/downloads/{download_id}/metadata",
        tags=[APITag.downloads],
        summary="Retrieve information on a file's state of preparation",
    )
    def get_download_metadata(
        task_id: str,
        download_id: str,
        wait_for_availability: bool = False,
    ) -> FileDownloadTaskDTO:
        sanitized_task_id = sanitize_uuid(task_id)
        sanitized_download_id = sanitize_uuid(download_id)

        # the task was successfully completed
        return filetransfer_manager.get_download_metadata(
            task_id=sanitized_task_id, download_id=sanitized_download_id, wait_for_availability=wait_for_availability
        )

    return bp
