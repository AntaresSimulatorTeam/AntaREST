import tempfile
from pathlib import Path
from typing import Optional

from starlette.background import BackgroundTasks

from antarest.core.config import Config


class FileTransferManager:
    _instance: Optional["FileTransferManager"] = None

    def __init__(self, config: Config):
        self.config = config
        self.tmp_dir = config.storage.tmp_dir

    @staticmethod
    def get_instance(config: Optional[Config]) -> "FileTransferManager":
        if FileTransferManager._instance is None:
            if config is None:
                raise AssertionError("FileTransferManager not initiated")
            else:
                FileTransferManager._instance = FileTransferManager(config)
        return FileTransferManager._instance

    @staticmethod
    def _cleanup_file(tmpfile: Path) -> None:
        tmpfile.unlink(missing_ok=True)

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
