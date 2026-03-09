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

from antarest.core.serde.ini_reader import IniReader
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.output.storage.output_storage import OutputDetails
from antarest.study.business.model.config.general_model import Mode

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


def extract_output_details(output_path: Path) -> OutputDetails:
    # TODO: add some basic checks
    parameters_path = output_path / "about-the-study" / "parameters.ini"
    ini_reader = IniReader(special_keys=DUPLICATE_KEYS)
    parameters_dict = ini_reader.read(parameters_path)
    general = parameters_dict["general"]
    output = parameters_dict["output"]
    mode = Mode(general["mode"])
    return OutputDetails(
        name=output_path.name,  # TODO: should it be re-built from data instead ?
        mode=mode,
        synthesis=output["synthesis"],
        by_year=general["year-by-year"],
        nb_years=general["nbyears"],
        archived=False,
    )


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
