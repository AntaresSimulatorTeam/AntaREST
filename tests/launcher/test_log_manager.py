import time
from pathlib import Path

from antarest.launcher.business.slurm_launcher.log_manager import SlurmLogManager


def test_reading():
    log_manager = SlurmLogManager(Path(""))

    log_manager.track(Path("/tmp/test"))
    log_manager.track(Path("/tmp/foo"))

    while True:
        time.sleep(1)