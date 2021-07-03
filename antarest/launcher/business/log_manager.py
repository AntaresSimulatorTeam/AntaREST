import logging
import time
from pathlib import Path
from threading import Thread
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class LogTailManager:
    BATCH_SIZE = 10

    def __init__(self, log_base_dir: Path) -> None:
        logger.info(f"Initiating Log manager")
        self.log_base_dir = log_base_dir
        self.tracked_logs: Dict[str, Thread] = {}

    def track(
        self, log_path: Optional[Path], handler: Callable[[str], None]
    ) -> None:
        if log_path is None:
            return None
        if str(log_path) in self.tracked_logs:
            logger.info(f"Already tracking log {log_path}")
            return None

        logger.info(f"Adding log {log_path} track")
        thread = Thread(
            target=lambda: self.follow(
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

    def stop_tracking(self, log_path: Optional[Path]) -> None:
        if log_path is None:
            return None
        log_path_key = str(log_path)
        if log_path_key in self.tracked_logs:
            del self.tracked_logs[log_path_key]

    def follow(
        self,
        log_file: Optional[Path],
        handler: Callable[[str], None],
        stop: Callable[[], bool],
    ) -> None:
        if not log_file or not log_file.exists():
            logger.warning(f"Failed to find {log_file}. Aborting log tracking")
            self.stop_tracking(log_file)
            return

        with open(log_file, "r") as fh:
            line = ""
            line_count = 0
            logger.info(f"Scanning {log_file}")
            while True:
                if stop():
                    break
                tmp = fh.readline()
                if not tmp:
                    if line:
                        logger.info(f"Calling handler for {log_file}")
                        handler(line)
                        line = ""
                        line_count = 0
                    time.sleep(0.1)
                else:
                    line += tmp
                    if line.endswith("\n"):
                        line_count += 1
                    if line_count >= LogTailManager.BATCH_SIZE:
                        logger.info(f"Calling handler for {log_file}")
                        handler(line)
                        line = ""
                        line_count = 0
