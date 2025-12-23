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
import zipfile
from pathlib import Path

import pytest

from antarest.study.model import StudySimSettingsDTO
from antarest.study.output.file.extract_metadata import extract_metadata


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    target = tmp_path / "STA-mini"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(target)
    return target / "STA-mini" / "output" / "20201014-1427eco"


def test_extract_output_metadata(output_path: Path):
    metadata = extract_metadata(output_path)
    assert metadata.name == "20201014-1427eco"
    assert metadata.type == "Economy"  # TODO: expected to be eco ?
    assert not metadata.archived
    assert metadata.settings == StudySimSettingsDTO(
        general={
            "mode": "Economy",
            "horizon": 2030,
            "nbyears": 1,
            "simulation.start": 1,
            "simulation.end": 7,
            "january.1st": "Monday",
            "first-month-in-year": "january",
            "first.weekday": "Monday",
            "leapyear": False,
            "year-by-year": False,
            "derated": False,
            "custom-ts-numbers": True,
            "user-playlist": True,
            "filtering": True,
            "active-rules-scenario": "default ruleset",
            "generate": "",
            "nbtimeseriesload": 1,
            "nbtimeserieshydro": 1,
            "nbtimeserieswind": 1,
            "nbtimeseriesthermal": 1,
            "nbtimeseriessolar": 1,
            "refreshtimeseries": "thermal",
            "intra-modal": "",
            "inter-modal": "",
            "refreshintervalload": 100,
            "refreshintervalhydro": 100,
            "refreshintervalwind": 100,
            "refreshintervalthermal": 1,
            "refreshintervalsolar": 100,
            "readonly": False,
        },
        input={"import": "thermal"},
        output={"synthesis": True, "storenewset": True, "archives": ""},
        optimization={
            "simplex-range": "week",
            "transmission-capacities": True,
            "link-type": "local",
            "include-constraints": True,
            "include-hurdlecosts": True,
            "include-tc-minstablepower": True,
            "include-tc-min-ud-time": True,
            "include-dayahead": True,
            "include-strategicreserve": True,
            "include-spinningreserve": True,
            "include-primaryreserve": True,
            "include-exportmps": False,
        },
        otherPreferences={
            "initial-reservoir-levels": "cold start",
            "power-fluctuations": "free modulations",
            "shedding-strategy": "share margins",
            "shedding-policy": "shave peaks",
            "unit-commitment-mode": "fast",
            "number-of-cores-mode": "maximum",
            "day-ahead-reserve-management": "global",
        },
        advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
        seedsMersenneTwister={
            "seed-tsgen-wind": 5489,
            "seed-tsgen-load": 1005489,
            "seed-tsgen-hydro": 2005489,
            "seed-tsgen-thermal": 3005489,
            "seed-tsgen-solar": 4005489,
            "seed-tsnumbers": 5005489,
            "seed-unsupplied-energy-costs": 6005489,
            "seed-spilled-energy-costs": 7005489,
            "seed-thermal-costs": 8005489,
            "seed-hydro-costs": 9005489,
            "seed-initial-reservoir-levels": 10005489,
        },
        playlist=[1],
    )
