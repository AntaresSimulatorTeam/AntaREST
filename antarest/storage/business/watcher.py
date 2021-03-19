import logging
import threading
from pathlib import Path
from time import time, sleep
from typing import List
from filelock import FileLock
from dataclasses import dataclass

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.model import StudyFolder
from antarest.storage.service import StorageService


logger = logging.getLogger(__name__)


class Watcher:
    LOCK = Path("watcher")
    DELAY = 1

    def __init__(self, config: Config, service: StorageService):
        self.service = service
        self.config = config
        self._get_lock()

        self.thread = (
            threading.Thread(target=self._loop) if self._get_lock() else None
        )

    def start(self) -> None:
        if self.thread:
            self.thread.start()

    def _get_lock(self) -> bool:
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
        studies: List[StudyFolder] = list()
        for name, workspace in self.config["storage.workspaces"].items():
            path = Path(workspace["path"])
            groups = [Group(id=g) for g in workspace.get("groups", [])]

            for folder in path.iterdir():
                if (folder / "study.antares").exists():
                    logger.info(f"Study {folder.name} found in {name}")
                    studies.append(StudyFolder(folder, name, groups))

        self.service.sync_studies_on_disk(studies)
