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
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from starlette.responses import FileResponse

from antarest.core.api_types import UuidStr
from antarest.core.filetransfer.model import FileDownloadDTO
from antarest.core.utils.web import APITag
from antarest.dependencies import FileTransferManagerDep, auth_required

logger = logging.getLogger(__name__)


def create_file_transfer_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.downloads], dependencies=[Depends(auth_required)])

    @bp.get("/downloads", summary="Get available downloads")
    def get_downloads(
        filetransfer_manager: FileTransferManagerDep,
    ) -> list[FileDownloadDTO]:
        logger.info("Retrieving downloads list.")
        return filetransfer_manager.list_downloads()

    @bp.get(
        "/downloads/{download_id}",
        summary="Retrieve download file",
    )
    def fetch_download(filetransfer_manager: FileTransferManagerDep, download_id: UuidStr) -> FileResponse:
        logger.info(f"Retrieving content for download {download_id}.")
        download = filetransfer_manager.fetch_download(download_id)
        return FileResponse(
            Path(download.path),
            headers={"Content-Disposition": f'attachment; filename="{download.filename}"'},
            media_type="application/zip",
        )

    @bp.get(
        "/downloads/{download_id}/metadata",
        summary="Retrieve information on a file's state of preparation",
    )
    def get_download_metadata(
        filetransfer_manager: FileTransferManagerDep,
        download_id: UuidStr,
        wait_for_availability: Annotated[
            bool, Query(description="If true, will wait for the download to be either ready or failed (max 1h).")
        ] = False,
    ) -> FileDownloadDTO:
        logger.info(f"Retrieving metadata for download {download_id} (waiting: {wait_for_availability}).")
        return filetransfer_manager.get_download_metadata(download_id, wait_for_availability)

    return bp
