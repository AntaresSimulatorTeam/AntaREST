import logging
import re
import threading
from pathlib import Path
from time import time, sleep
from typing import List

from filelock import FileLock  # type: ignore

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group
from antarest.study.model import StudyFolder, DEFAULT_WORKSPACE_NAME
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class Watcher:
    """
    Files Watcher to listen raw studies changes and trigger a database update.
    """

    LOCK = Path("watcher")
    DELAY = 2

    def __init__(self, config: Config, service: StudyService):
        self.service = service
        self.config = config

        self.thread = (
            threading.Thread(target=self._loop, daemon=True)
            if not config.storage.watcher_lock or Watcher._get_lock()
            else None
        )

    def start(self) -> None:
        """
        Start watching
        Returns:

        """
        if self.thread:
            self.thread.start()

    @staticmethod
    def _get_lock() -> bool:
        """
        Force watcher to run only one by access a lock on filesystem.

        Returns: true if watcher get the lock, false else.

        """
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
        """
        Scan recursively list of studies present on disk. Send updated list to study service.
        Returns:

        """

        def rec_scan(
            path: Path,
            workspace: str,
            groups: List[Group],
            filter_in: List[str],
            filter_out: List[str],
        ) -> List[StudyFolder]:
            try:
                if (path / "study.antares").exists():
                    logger.debug(f"Study {path.name} found in {workspace}")
                    return [StudyFolder(path, workspace, groups)]
                else:
                    folders: List[StudyFolder] = list()
                    if path.is_dir():
                        for child in path.iterdir():
                            try:
                                if (
                                    child.is_dir()
                                    and any(
                                        [
                                            re.search(regex, child.stem)
                                            for regex in filter_in
                                        ]
                                    )
                                    and not any(
                                        [
                                            re.search(regex, child.stem)
                                            for regex in filter_out
                                        ]
                                    )
                                ):
                                    folders = folders + rec_scan(
                                        child,
                                        workspace,
                                        groups,
                                        filter_in,
                                        filter_out,
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Failed to scan dir {child}", exc_info=e
                                )
                    return folders
            except Exception as e:
                logger.error(f"Failed to scan dir {path}", exc_info=e)
                return []

        studies: List[StudyFolder] = list()
        for name, workspace in self.config.storage.workspaces.items():
            if name != DEFAULT_WORKSPACE_NAME:
                path = Path(workspace.path)
                groups = [Group(id=g) for g in workspace.groups]
                studies = studies + rec_scan(
                    path,
                    name,
                    groups,
                    workspace.filter_in,
                    workspace.filter_out,
                )

        with db():
            self.service.sync_studies_on_disk(studies)
