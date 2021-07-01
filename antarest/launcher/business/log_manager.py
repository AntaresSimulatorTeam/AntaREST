import logging
import time
from pathlib import Path
from threading import Thread
from typing import Callable, Dict

logger = logging.getLogger(__name__)


class LogTailManager:
    def __init__(self, log_base_dir: Path) -> None:
        logger.info(f"Initiating Log manager")
        self.log_base_dir = log_base_dir
        self.tracked_logs: Dict[str, Thread] = {}

    def track(self, log_path: Path, handler: Callable[[str], None]) -> None:
        logger.info(f"Adding log {log_path} track")
        thread = Thread(
            target=lambda: LogTailManager.follow(
                log_path, handler, self._stop_tracking(str(log_path))
            ),
            daemon=True,
        )
        self.tracked_logs[str(log_path)] = thread
        thread.start()

    def _stop_tracking(self, log_path: str) -> Callable[[], bool]:
        def stop() -> bool:
            return log_path not in self.tracked_logs

        return stop

    def stop_tracking(self, log_path: Path) -> None:
        del self.tracked_logs[str(log_path)]

    @staticmethod
    def follow(
        log_file: Path,
        handler: Callable[[str], None],
        stop: Callable[[], bool],
    ) -> None:
        with open(log_file, "r") as fh:
            line = ""
            logger.info(f"Scanning {log_file}")
            while True:
                if stop():
                    break
                tmp = fh.readline()
                if not tmp:
                    time.sleep(0.1)
                else:
                    line += tmp
                    if line.endswith("\n"):
                        logger.info(f"Calling handler for {log_file}")
                        handler(line)
                        line = ""
