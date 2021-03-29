import logging
import threading
from pathlib import Path
from time import time, sleep
from typing import List
from filelock import FileLock  # type: ignore

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.config import get_config
from antarest.storage.model import StudyFolder, DEFAULT_WORKSPACE_NAME
from antarest.storage.service import StorageService


logger = logging.getLogger(__name__)


class Watcher:
    LOCK = Path("watcher")
    DELAY = 2

    def __init__(self, config: Config, service: StorageService):
        self.service = service
        self.config = get_config(config)

        self.thread = (
            threading.Thread(target=self._loop, daemon=True)
            if Watcher._get_lock()
            else None
        )

    def start(self) -> None:
        if self.thread:
            self.thread.start()

    @staticmethod
    def _get_lock() -> bool:
        with FileLock(f"{Watcher.LOCK}.lock"):
            start = (
                int(f"0{Watcher.LOCK.read_text()}")
                if Watcher.LOCK.exists()
                else 0
            )
            now = int(time())
            if now - start > Watcher.DELAY:
                Watcher.LOCK.write_text(str(now))
                logger.info("Watcher get lock")
                return True
            else:
                logger.info("Watcher doesn't get lock")
                return False

    def _loop(self) -> None:
        while True:
            self._scan()
            sleep(2)

    def _scan(self) -> None:
        def rec_scan(
            path: Path, workspace: str, groups: List[Group]
        ) -> List[StudyFolder]:
            try:
                if (path / "study.antares").exists():
                    logger.debug(f"Study {path.name} found in {workspace}")
                    return [StudyFolder(path, workspace, groups)]
                else:
                    folders: List[StudyFolder] = list()
                    if path.is_dir():
                        for child in path.iterdir():
                            folders = folders + rec_scan(
                                child, workspace, groups
                            )
                    return folders
            except Exception as e:
                logger.error(f"Failed to scan dir {path}", exc_info=e)
                return []

        studies: List[StudyFolder] = list()
        for name, workspace in self.config.workspaces.items():
            if name != DEFAULT_WORKSPACE_NAME:
                path = Path(workspace.path)
                groups = [Group(id=g) for g in workspace.groups]
                studies = studies + rec_scan(path, name, groups)

        self.service.sync_studies_on_disk(studies)
