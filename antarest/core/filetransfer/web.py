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
import concurrent.futures
import http
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.tasks.model import TaskStatus
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskService
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth


def create_file_transfer_api(
    filetransfer_manager: FileTransferManager, task_service: ITaskService, config: Config
) -> APIRouter:
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
        summary="Retrieve download file or information on the file's state of preparation",
    )
    def get_download_metadata(
        task_id: str,
        download_id: str,
        wait_for_availability: bool = False,
        timeout: int = DEFAULT_AWAIT_MAX_TIMEOUT,
    ) -> FileResponse:
        sanitized_task_id = sanitize_uuid(task_id)
        task = task_service.status_task(sanitized_task_id)

        # the user ask for a timeout
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            if wait_for_availability:
                try:
                    task_service.await_task(task_id=sanitized_task_id, timeout_sec=timeout)
                except concurrent.futures.TimeoutError:
                    raise HTTPException(
                        status_code=http.HTTPStatus.EXPECTATION_FAILED,
                        detail=f"The requested file is still in process after waiting for {timeout} seconds.",
                    )
            # the user did not ask for a timeout
            else:
                raise HTTPException(
                    status_code=http.HTTPStatus.EXPECTATION_FAILED, detail="The requested file is still in process."
                )

        task = task_service.status_task(sanitized_task_id)  # update task status

        # the task could not be completed
        if task.status != TaskStatus.COMPLETED:
            raise HTTPException(
                status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"The requested file was not successfully processed: {task.result.message}",  # type: ignore
            )

        try:
            file_download = filetransfer_manager.fetch_download(download_id)
        except Exception as e:
            raise HTTPException(
                status_code=e.args[0],
                detail=f"Impossible to retrieve the requested file: {e.args[1]}",
            ) from e

        # the task was successfully completed
        return FileResponse(
            path=file_download.path,
            status_code=http.HTTPStatus.OK,
            headers={"Content-Disposition": f'attachment; filename="{file_download.filename}"'},
        )

    return bp
