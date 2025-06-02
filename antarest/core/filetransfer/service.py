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

import datetime
import http
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException
from starlette.background import BackgroundTasks

from antarest.core.config import Config
from antarest.core.filetransfer.model import (
    FileDownload,
    FileDownloadDTO,
    FileDownloadNotFound,
    FileDownloadNotReady,
    FileDownloadTaskDTO,
)
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.tasks.model import TaskStatus
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskService
from antarest.login.utils import get_current_user, require_current_user

logger = logging.getLogger(__name__)


class FileTransferManager:
    _instance: Optional["FileTransferManager"] = None

    def __init__(
        self,
        repository: FileDownloadRepository,
        event_bus: IEventBus,
        task_service: ITaskService,
        config: Config,
    ):
        self.config = config
        self.repository = repository
        self.event_bus = event_bus
        self.task_service = task_service
        self.tmp_dir = config.storage.tmp_dir
        self.download_default_expiration_timeout_minutes = config.storage.download_default_expiration_timeout_minutes

    @staticmethod
    def _cleanup_file(tmpfile: Path) -> None:
        tmpfile.unlink(missing_ok=True)

    def request_download(
        self,
        filename: str,
        name: Optional[str] = None,
        use_notification: bool = True,
        expiration_time_in_minutes: int = 0,
    ) -> FileDownload:
        fh, path = tempfile.mkstemp(dir=self.tmp_dir, suffix=filename)
        os.close(fh)
        tmpfile = Path(path)
        owner = get_current_user()
        download = FileDownload(
            id=str(uuid.uuid4()),
            filename=filename,
            name=name or filename,
            ready=False,
            path=str(tmpfile),
            owner=owner.impersonator if owner is not None else None,
            expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(
                minutes=expiration_time_in_minutes or self.download_default_expiration_timeout_minutes
            ),
        )
        self.repository.add(download)
        if use_notification:
            self.event_bus.push(
                Event(
                    type=EventType.DOWNLOAD_CREATED,
                    payload=download.to_dto(),
                    permissions=(
                        PermissionInfo(owner=owner.impersonator)
                        if owner
                        else PermissionInfo(public_mode=PublicMode.READ)
                    ),
                )
            )
        return download

    def set_ready(self, download_id: str, use_notification: bool = True) -> None:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        download.ready = True
        self.repository.save(download)
        if use_notification:
            self.event_bus.push(
                Event(
                    type=EventType.DOWNLOAD_READY,
                    payload=download.to_dto(),
                    permissions=(
                        PermissionInfo(owner=download.owner)
                        if download.owner
                        else PermissionInfo(public_mode=PublicMode.READ)
                    ),
                )
            )

    def fail(self, download_id: str, reason: str = "") -> None:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        download.failed = True
        download.error_message = reason
        self.repository.save(download)
        self.event_bus.push(
            Event(
                type=EventType.DOWNLOAD_FAILED,
                payload=download.to_dto(),
                permissions=(
                    PermissionInfo(owner=download.owner)
                    if download.owner
                    else PermissionInfo(public_mode=PublicMode.READ)
                ),
            )
        )

    def remove(self, download_id: str) -> None:
        download = self.repository.get(download_id)
        owner = download.owner if download else None
        self.repository.delete(download_id)
        self.event_bus.push(
            Event(
                type=EventType.DOWNLOAD_EXPIRED,
                payload=download_id,
                permissions=PermissionInfo(owner=owner) if owner else PermissionInfo(public_mode=PublicMode.READ),
            )
        )

    def request_tmp_file(self, background_tasks: BackgroundTasks) -> Path:
        """
        Returns a new tmp path that will be deleted at the end of the request
        TODO: should be deleted in case of exception before request end !!!

        Args:
            background_tasks: injection of the BackgroundTasks service

        Returns:
            a fresh tmp file path
        """
        fh, path = tempfile.mkstemp(dir=self.tmp_dir)
        os.close(fh)
        tmppath = Path(path)
        background_tasks.add_task(FileTransferManager._cleanup_file, tmppath)
        return tmppath

    def list_downloads(self) -> List[FileDownloadDTO]:
        user = require_current_user()
        downloads = self.repository.get_all() if user.is_site_admin() else self.repository.get_all(user.impersonator)
        self._clean_up_expired_downloads(downloads)
        return [d.to_dto() for d in downloads]

    def _clean_up_expired_downloads(self, file_downloads: List[FileDownload]) -> None:
        now = datetime.datetime.utcnow()
        to_remove = []
        for file_download in file_downloads:
            if file_download.expiration_date is not None and file_download.expiration_date <= now:
                to_remove.append(file_download)
        for file_download in to_remove:
            logger.info(f"Removing expired download {file_download}")
            file_downloads.remove(file_download)
            download_id = file_download.id
            download_owner = file_download.owner
            try:
                os.unlink(file_download.path)
            except Exception as e:
                logger.error(
                    f"Failed to remove file download {file_download.path}",
                    exc_info=e,
                )
            self.repository.delete(file_download.id)
            self.event_bus.push(
                Event(
                    type=EventType.DOWNLOAD_EXPIRED,
                    payload=download_id,
                    permissions=(
                        PermissionInfo(owner=download_owner)
                        if download_owner
                        else PermissionInfo(public_mode=PublicMode.READ)
                    ),
                )
            )

    def fetch_download(self, download_id: str) -> FileDownload:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        user = get_current_user()
        if not user or not (user.is_site_admin() or download.owner == user.impersonator):
            raise UserHasNotPermissionError()

        if not download.ready:
            raise FileDownloadNotReady()

        return download

    def get_download_metadata(self, task_id: str, download_id: str, wait_for_availability: bool) -> FileDownloadTaskDTO:
        task = self.task_service.status_task(task_id)

        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()
        file = download.to_dto()

        # the user wants to wait for the download to be available
        if wait_for_availability:
            end = time.time() + DEFAULT_AWAIT_MAX_TIMEOUT
            while task.status in [TaskStatus.PENDING, TaskStatus.RUNNING] and time.time() < end:
                task = self.task_service.status_task(task_id)
                time.sleep(2)

        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise HTTPException(status_code=http.HTTPStatus.REQUEST_TIMEOUT, detail="File is still in process.")

        if task.status == TaskStatus.FAILED:
            raise HTTPException(
                status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"File was not successfully processed: {task.result.message}.",  # type: ignore
            )

        return FileDownloadTaskDTO(task=task.id, file=file)
