# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import logging
from pathlib import Path

from fastapi import APIRouter
from starlette.responses import FileResponse

from antarest.core.api_types import SanitizedStr
from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_file_transfer_api(filetransfer_manager: FileTransferManager, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.downloads], dependencies=[auth.required()])

    @bp.get("/downloads", summary="Get available downloads")
    def get_downloads() -> list[FileDownloadDTO]:
        logger.info("Retrieving downloads list.")
        return filetransfer_manager.list_downloads()

    @bp.get(
        "/downloads/{download_id}",
        summary="Retrieve download file",
    )
    def fetch_download(download_id: SanitizedStr) -> FileResponse:
        sanitized_download_id = sanitize_uuid(download_id)
        logger.info(f"Retrieving content for download {sanitized_download_id}.")
        download = filetransfer_manager.fetch_download(sanitized_download_id)
        return FileResponse(
            Path(download.path),
            headers={"Content-Disposition": f'attachment; filename="{download.filename}"'},
            media_type="application/zip",
        )

    @bp.get(
        "/downloads/{download_id}/metadata",
        summary="Retrieve information on a file's state of preparation",
    )
    def get_download_metadata(download_id: SanitizedStr, wait_for_availability: bool = False) -> FileDownloadDTO:
        sanitized_download_id = sanitize_uuid(download_id)
        logger.info(f"Retrieving metadata for download {sanitized_download_id} (waiting: {wait_for_availability}).")
        return filetransfer_manager.get_download_metadata(sanitized_download_id, wait_for_availability)

    return bp
