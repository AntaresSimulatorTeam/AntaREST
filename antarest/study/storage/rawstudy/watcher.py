import logging
import re
import threading
from html import escape
from pathlib import Path
from time import time, sleep
from typing import List

from filelock import FileLock

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

    def __init__(self, config: Config, service: StudyService):
        self.service = service
        self.config = config
        self.should_stop = False
        self.thread = (
            threading.Thread(target=self._loop, daemon=True)
            if not config.storage.watcher_lock
            or Watcher._get_lock(config.storage.watcher_lock_delay)
            else None
        )

    def start(self, threaded: bool = True) -> None:
        """
        Start watching
        Returns:

        """
        self.should_stop = False
        if threaded:
            if self.thread and not self.thread.is_alive():
                self.thread.start()
        else:
            self._loop()

    def stop(self) -> None:
        self.should_stop = True

    @staticmethod
    def _get_lock(lock_delay: int) -> bool:
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
            if now - start > lock_delay:
                Watcher.LOCK.write_text(str(now))
                logger.info("Watcher get lock")
                return True
            else:
                logger.info("Watcher doesn't get lock")
                return False

    def _loop(self) -> None:
        try:
            logger.info(
                "Removing duplicates, this is a temporary fix that should be removed when previous duplicates are removed"
            )
            with db():
                self.service.remove_duplicates()
        except Exception as e:
            logger.error(
                "Unexpected error when removing duplicates", exc_info=e
            )

        while True:
            try:
                if not self.should_stop:
                    self._scan()
            except Exception as e:
                logger.error(
                    "Unexpected error when scanning workspaces", exc_info=e
                )
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
                if (path / "AW_NO_SCAN").exists():
                    logger.info(
                        f"No scan directive file found. Will skip further scan of folder {path}"
                    )
                    return []
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
                                            re.search(regex, child.name)
                                            for regex in filter_in
                                        ]
                                    )
                                    and not any(
                                        [
                                            re.search(regex, child.name)
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
                groups = [
                    Group(id=escape(g), name=escape(g))
                    for g in workspace.groups
                ]
                studies = studies + rec_scan(
                    path,
                    name,
                    groups,
                    workspace.filter_in,
                    workspace.filter_out,
                )

        with db():
            self.service.sync_studies_on_disk(studies)
