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
from datetime import datetime
from pathlib import Path
from typing import IO
from zipfile import ZipFile

from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode

PARAMETERS_TEMPLATE = """
[general]
mode = {mode}
simulation.start = 1
simulation.end = 7
horizon = 2000
first-month-in-year = january
first.weekday = Monday
january.1st = Monday
leapyear = False
nbyears = 1
user-playlist = True
year-by-year = False
geographic-trimming = True
thematic-trimming = False
derated = False
custom-scenario = False
active-rules-scenario = default ruleset
generate = hydro, thermal
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeserieswind = 1
nbtimeseriesthermal = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 0
refreshintervalhydro = 5
refreshintervalwind = 5
refreshintervalthermal = 0
refreshintervalsolar = 0
readonly = False

[input]
import = 

[output]
synthesis = False
storenewset = False
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = True
include-hurdlecosts = True
include-tc-minstablepower = True
include-tc-min-ud-time = True
include-dayahead = True
include-strategicreserve = True
include-spinningreserve = True
include-primaryreserve = True
include-exportmps = none
include-exportstructure = False
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = False
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = True
price-taking-order = DENS
include-hurdle-cost-csr = False
check-csr-cost-function = False
threshold-initiate-curtailment-sharing-rule = 0.0
threshold-display-local-matching-rule-violations = 0.0
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = accurate shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

[seeds - Mersenne Twister]
seed-tsgen-wind = 5489
seed-tsgen-load = 5489
seed-tsgen-hydro = 5489
seed-tsgen-thermal = 5489
seed-tsgen-solar = 5489
seed-tsnumbers = 5489
seed-unsupplied-energy-costs = 6005489
seed-spilled-energy-costs = 7005489
seed-thermal-costs = 8005489
seed-hydro-costs = 9005489
seed-initial-reservoir-levels = 10005489

[compatibility]
hydro-pmax = daily
"""

INFO_ANTARES_OUTPUT_TEMPLATE = """
[general]
version = {version}
name = {name}
mode = {mode}
date = 2026.02.16 - 08:56
title = 2026.02.16 - 08:56
timestamp = {timestamp}
"""

TIMESTAMP_FORMAT = "%Y%m%d-%H%M"


def output_name_to_tuple(name: str) -> tuple[datetime, Mode, str]:
    timestamp_str = name[0:13]
    mode_str = name[13:16]
    remainder = name[16:]
    timestamp = datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
    mode = Mode.from_output_suffix(mode_str)
    name = ""
    if remainder.startswith("-"):
        name = remainder[1:]
    return timestamp, mode, name


def output_tuple_to_name(timestamp: datetime, mode: Mode = Mode.ECONOMY, name: str = "") -> str:
    formatted_timestamp = timestamp.strftime(TIMESTAMP_FORMAT)
    res = f"{formatted_timestamp}{mode.get_output_suffix()}"
    if name:
        res += f"-{name}"
    return res


def create_minimal_output_zip(
    target: Path | IO[bytes],
    timestamp: datetime | str,
    mode: Mode = Mode.ECONOMY,
    name: str = "",
) -> None:
    """
    Creates a minimal valid output content into a zip file that can be imported through the API.
    """
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    with ZipFile(target, "w") as zf:
        zf.writestr("about-the-study/parameters.ini", PARAMETERS_TEMPLATE)
        info_content = INFO_ANTARES_OUTPUT_TEMPLATE.format(
            version="9.2", name=name, mode=mode.value, timestamp=timestamp.timestamp()
        )
        zf.writestr("info.antares-output", info_content)


def create_minimal_output_zip_from_name(
    target: Path | IO[bytes],
    output_name: str,
) -> None:
    """
    Creates a minimal valid output content into a zip file that can be imported through the API.
    """
    timestamp, mode, name = output_name_to_tuple(output_name)
    create_minimal_output_zip(target, timestamp, mode, name)
