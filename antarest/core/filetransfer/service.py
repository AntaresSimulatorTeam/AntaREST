import datetime
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List

from starlette.background import BackgroundTasks

from antarest.core.config import Config
from antarest.core.filetransfer.model import (
    FileDownload,
    FileDownloadDTO,
    FileDownloadNotFound,
    FileDownloadNotReady,
)
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import (
    RequestParameters,
    MustBeAuthenticatedError,
    UserHasNotPermissionError,
)


logger = logging.getLogger(__name__)


class FileTransferManager:
    _instance: Optional["FileTransferManager"] = None

    def __init__(
        self,
        repository: FileDownloadRepository,
        event_bus: IEventBus,
        config: Config,
    ):
        self.config = config
        self.repository = repository
        self.event_bus = event_bus
        self.tmp_dir = config.storage.tmp_dir
        self.download_default_expiration_timeout_minutes = (
            config.storage.download_default_expiration_timeout_minutes
        )

    @staticmethod
    def _cleanup_file(tmpfile: Path) -> None:
        tmpfile.unlink(missing_ok=True)
        pass

    def request_download(
        self,
        filename: str,
        name: Optional[str] = None,
        owner: Optional[JWTUser] = None,
    ) -> FileDownload:
        fh, path = tempfile.mkstemp(dir=self.tmp_dir, suffix=filename)
        os.close(fh)
        tmpfile = Path(path)
        download = FileDownload(
            id=str(uuid.uuid4()),
            filename=filename,
            name=name or filename,
            ready=False,
            path=str(tmpfile),
            owner=owner.impersonator if owner is not None else None,
            expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(
                minutes=self.download_default_expiration_timeout_minutes
            ),
        )
        self.repository.add(download)
        self.event_bus.push(
            Event(
                type=EventType.DOWNLOAD_CREATED,
                payload=download.to_dto(),
                permissions=PermissionInfo(owner=owner.impersonator)
                if owner
                else PermissionInfo(public_mode=PublicMode.READ),
            )
        )
        return download

    def set_ready(self, download_id: str) -> None:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        download.ready = True
        self.repository.save(download)
        self.event_bus.push(
            Event(
                type=EventType.DOWNLOAD_READY,
                payload=download.to_dto(),
                permissions=PermissionInfo(owner=download.owner)
                if download.owner
                else PermissionInfo(public_mode=PublicMode.READ),
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
                permissions=PermissionInfo(owner=download.owner)
                if download.owner
                else PermissionInfo(public_mode=PublicMode.READ),
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
                permissions=PermissionInfo(owner=owner)
                if owner
                else PermissionInfo(public_mode=PublicMode.READ),
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

    def list_downloads(
        self, params: RequestParameters
    ) -> List[FileDownloadDTO]:
        if not params.user:
            raise MustBeAuthenticatedError()
        downloads = (
            self.repository.get_all()
            if params.user.is_site_admin()
            else self.repository.get_all(params.user.impersonator)
        )
        self._clean_up_expired_downloads(downloads)
        return [d.to_dto() for d in downloads]

    def _clean_up_expired_downloads(
        self, file_downloads: List[FileDownload]
    ) -> None:
        now = datetime.datetime.utcnow()
        to_remove = []
        for file_download in file_downloads:
            if (
                file_download.expiration_date is not None
                and file_download.expiration_date <= now
            ):
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
                    permissions=PermissionInfo(owner=download_owner)
                    if download_owner
                    else PermissionInfo(public_mode=PublicMode.READ),
                )
            )

    def fetch_download(
        self, download_id: str, params: RequestParameters
    ) -> FileDownload:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        if not params.user or not (
            params.user.is_site_admin()
            or download.owner == params.user.impersonator
        ):
            raise UserHasNotPermissionError()

        if not download.ready:
            raise FileDownloadNotReady()

        return download
