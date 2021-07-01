import os
import time
from pathlib import Path

from antarest.launcher.business.slurm_launcher.log_manager import (
    SlurmLogManager,
)

import logging

logging.basicConfig(level=logging.DEBUG)


def test_reading(tmp_path: Path):
    log_manager = SlurmLogManager(tmp_path)

    logs = []

    def handler(line: str):
        logs.append(line)

    log1 = tmp_path / "foo"
    log2 = tmp_path / "test"
    log1.touch()
    log2.touch()

    log_manager.track(log1, handler)
    log_manager.track(log2, handler)

    with open(log1, "a") as fh:
        fh.write("hello\n")
    with open(log2, "a") as fh:
        fh.write("hello\n")
    with open(log2, "a") as fh:
        fh.write("world\n")

    assert len(logs) == 0
    count = 5
    while count > 0 and len(logs) == 0:
        count -= 1
        time.sleep(1)

    assert len(logs) > 0

    logs.clear()
    log_manager.stop_tracking(log1)
    with open(log1, "a") as fh:
        fh.write("world\n")

    count = 2
    while count > 0:
        count -= 1
        time.sleep(1)
    assert len(logs) == 0
