# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import time
from pathlib import Path

from antarest.launcher.adapters.log_manager import LogTailManager

logging.basicConfig(level=logging.DEBUG)


def test_reading(tmp_path: Path):
    log_manager = LogTailManager(tmp_path)

    logs = []

    def handler(line: str):
        logs.append(line)

    log1 = tmp_path / "foo"
    log2 = tmp_path / "test"
    log1.touch()
    log2.touch()

    log_manager.track(log1, handler)
    log_manager.track(log2, handler)

    assert len(logs) == 0

    with open(log1, "a") as fh:
        fh.write("hello\n")
    with open(log2, "a") as fh:
        fh.write("hello\n")
    with open(log2, "a") as fh:
        fh.write("world\n")

    timeout = 0.5
    interval = 0.01
    elapsed = 0
    while elapsed < timeout and len(logs) == 0:
        time.sleep(interval)
        elapsed += interval

    assert len(logs) > 0

    log_manager.stop_tracking(log1)
    log_manager.stop_tracking(log2)
    logs.clear()
    with open(log1, "a") as fh:
        fh.write("world\n")

    timeout = 0.5
    interval = 0.01
    elapsed = 0
    while elapsed < timeout:
        assert len(logs) == 0
        time.sleep(interval)
        elapsed += interval
