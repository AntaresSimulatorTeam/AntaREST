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
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.requests import (
    RequestParameters,
    MustBeAuthenticatedError,
    UserHasNotPermissionError,
)


class FileTransferManager:
    _instance: Optional["FileTransferManager"] = None

    def __init__(self,
                 repository: FileDownloadRepository,
                 event_bus: IEventBus,
                 config: Config):
        self.config = config
        self.repository = repository
        self.event_bus = event_bus
        self.tmp_dir = config.storage.tmp_dir

    @staticmethod
    def get_instance() -> "FileTransferManager":
        if FileTransferManager._instance is None:
            raise AssertionError("FileTransferManager not initiated")
        return FileTransferManager._instance

    @staticmethod
    def _cleanup_file(tmpfile: Path) -> None:
        tmpfile.unlink(missing_ok=True)

    def request_download(
        self, filename: str, name: Optional[str] = None
    ) -> FileDownload:
        tmpfile = Path(tempfile.mktemp(dir=self.tmp_dir))
        download = FileDownload(
            id=str(uuid.uuid4()),
            filename=filename,
            name=name or filename,
            ready=False,
            path=str(tmpfile),
        )
        self.repository.add(download)
        return download

    def set_ready(self, download_id: str):
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        download.ready = True
        self.repository.save(download)

    def request_tmp_file(self, background_tasks: BackgroundTasks) -> Path:
        """
        Returns a new tmp path that will be deleted at the end of the request
        TODO: should be deleted in case of exception before request end !!!

        Args:
            background_tasks: injection of the BackgroundTasks service

        Returns:
            a fresh tmp file path
        """
        tmpfile = Path(tempfile.mktemp(dir=self.tmp_dir))
        background_tasks.add_task(FileTransferManager._cleanup_file, tmpfile)
        return tmpfile

    def list_downloads(
        self, params: RequestParameters
    ) -> List[FileDownloadDTO]:
        if not params.user:
            raise MustBeAuthenticatedError()
        if params.user.is_site_admin():
            return [d.to_dto() for d in self.repository.get_all()]
        return [
            d.to_dto()
            for d in self.repository.get_all(params.user.impersonator)
        ]

    def fetch_download(
        self, download_id: str, params: RequestParameters
    ) -> FileDownload:
        download = self.repository.get(download_id)
        if not download:
            raise FileDownloadNotFound()

        if (
            not params.user.is_site_admin()
            or download.owner != params.user.impersonator
        ):
            raise UserHasNotPermissionError()

        if not download.ready:
            raise FileDownloadNotReady()

        return download
