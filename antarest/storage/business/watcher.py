import logging
import threading
from pathlib import Path
from time import time, sleep
from typing import List
from dataclasses import dataclass

from antarest.common.config import Config
from antarest.login.model import Group
from antarest.storage.model import StudyFolder
from antarest.storage.service import StorageService


logger = logging.getLogger(__name__)


class Watcher:
    LOCK = Path("watcher.lock")
    DELAY = 1

    def __init__(self, config: Config, service: StorageService):
        self.service = service
        self.config = config

        self.thread = (
            threading.Thread(target=self._loop) if self._get_lock() else None
        )

    def start(self) -> None:
        if self.thread:
            self.thread.start()

    def _get_lock(self) -> bool:
        return True

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
