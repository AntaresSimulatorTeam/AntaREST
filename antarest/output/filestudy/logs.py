# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from pathlib import Path

from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType


def find_simulation_log(output_dir: Path, log_type: LogType) -> Path | None:
    log_locations = {
        LogType.STDOUT: [
            output_dir / "antares-out.log",
            output_dir / "simulation.log",
        ],
        LogType.STDERR: [
            output_dir / "antares-err.log",
        ],
    }
    return next((loc for loc in log_locations[log_type] if loc.is_file()), None)


def find_logs(output_dir: Path) -> SimulationLogs:
    return SimulationLogs(
        out=find_simulation_log(output_dir, LogType.STDOUT), err=find_simulation_log(output_dir, LogType.STDERR)
    )
