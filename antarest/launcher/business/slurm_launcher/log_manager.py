import asyncio
import time
from asyncio import Task
from collections import Iterator
from pathlib import Path
from threading import Lock
from typing import Callable, Dict, Coroutine


class SlurmLogManager:

    def __init__(self, slurm_workspace: Path):
        self.slurm_workspace = slurm_workspace
        self.tracked_logs: Dict[str, Task] = {}
        self.lock = Lock()
        self.loop = asyncio.get_event_loop()

    def track(self, log_path: Path):
        self.tracked_logs[str(log_path)] = self.loop.create_task(self.follow(log_path, self._on_log_lines(str(log_path))))

    def stop_track(self, log_path: Path):
        self.tracked_logs[str(log_path)].cancel()

    def _on_log_lines(self, id: str):
        def on_line(line: str):
            print(f"{id}: {line}")
        return on_line

    async def follow(self, log_file, handler: Callable[[str], None]) -> None:
        with open(log_file, 'r') as fh:
            line = ''
            while True:
                tmp = fh.readline()
                if tmp is not None:
                    line += tmp
                    if line.endswith("\n"):
                        handler(line)
                        line = ''
                else:
                    await asyncio.sleep(0.1)


