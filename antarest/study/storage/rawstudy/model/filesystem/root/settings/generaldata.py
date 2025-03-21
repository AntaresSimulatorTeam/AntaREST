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

from copy import deepcopy
from typing import Any, Dict

from antarest.core.serde.ini_reader import IniReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_7_0,
    STUDY_VERSION_7_1,
    STUDY_VERSION_7_2,
    STUDY_VERSION_8,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_2,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


class GeneralData(IniFileNode):
    TYPES: Dict[str, Dict[str, Any]] = {
        "general": {
            "mode": str,
            "horizon": (int, str),
            "nbyears": int,
            "simulation.start": int,
            "simulation.end": int,
            "january.1st": str,
            "first-month-in-year": str,
            "first.weekday": str,
            "leapyear": bool,
            "year-by-year": bool,
            "derated": bool,
            "custom-ts-numbers": bool,
            "user-playlist": bool,
            "filtering": bool,
            "active-rules-scenario": str,
            "generate": str,
            "nbtimeseriesload": int,
            "nbtimeserieshydro": int,
            "nbtimeserieswind": int,
            "nbtimeseriesthermal": int,
            "nbtimeseriessolar": int,
            "refreshtimeseries": str,
            "intra-modal": str,
            "inter-modal": str,
            "refreshintervalload": int,
            "refreshintervalhydro": int,
            "refreshintervalwind": int,
            "refreshintervalthermal": int,
            "refreshintervalsolar": int,
            "readonly": bool,
        },
        "input": {"import": str},
        "output": {
            "synthesis": bool,
            "storenewset": bool,
            "archives": str,
        },
        "optimization": {
            "simplex-range": str,
            "transmission-capacities": str,
            "include-constraints": bool,
            "include-hurdlecosts": bool,
            "include-tc-minstablepower": bool,
            "include-tc-min-ud-time": bool,
            "include-dayahead": bool,
            "include-strategicreserve": bool,
            "include-spinningreserve": bool,
            "include-primaryreserve": bool,
            "include-exportmps": bool,
        },
        "other preferences": {
            "power-fluctuations": str,
            "shedding-strategy": str,
            "shedding-policy": str,
            "unit-commitment-mode": str,
            "number-of-cores-mode": str,
            "day-ahead-reserve-management": str,
        },
        "advanced parameters": {
            "accuracy-on-correlation": str,
            "adequacy-block-size": int,
        },
        "seeds - Mersenne Twister": {
            "seed-tsgen-wind": int,
            "seed-tsgen-load": int,
            "seed-tsgen-hydro": int,
            "seed-tsgen-thermal": int,
            "seed-tsgen-solar": int,
            "seed-tsnumbers": int,
            "seed-unsupplied-energy-costs": int,
            "seed-spilled-energy-costs": int,
            "seed-thermal-costs": int,
            "seed-hydro-costs": int,
            "seed-initial-reservoir-levels": int,
        },
    }

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = deepcopy(GeneralData.TYPES)
        general = types["general"]
        optimization = types["optimization"]
        other_preferences = types["other preferences"]
        study_version = config.version
        if study_version >= STUDY_VERSION_6_5:
            other_preferences["initial-reservoir-levels"] = str
        if study_version >= STUDY_VERSION_7_0:
            optimization["link-type"] = str
        if study_version >= STUDY_VERSION_7_1:
            general["thematic-trimming"] = bool
            general["geographic-trimming"] = bool
            del general["filtering"]
        if study_version >= STUDY_VERSION_7_2:
            other_preferences["hydro-pricing-mode"] = str
        if study_version >= STUDY_VERSION_8:
            other_preferences["hydro-heuristic-policy"] = str
            optimization["include-exportstructure"] = bool
            optimization["include-unfeasible-problem-behavior"] = str
            general["custom-scenario"] = bool
            del general["custom-ts-numbers"]
        if study_version >= STUDY_VERSION_8_1:
            other_preferences["renewable-generation-modelling"] = str
        if study_version >= STUDY_VERSION_8_3:
            types["adequacy patch"] = {
                "include-adq-patch": bool,
                "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step": bool,
                "set-to-null-ntc-between-physical-out-for-first-step": bool,
            }
            optimization["include-split-exported-mps"] = bool
            # include-exportmps: none, optim-1, optim-2, both-optims
            optimization["include-exportmps"] = str
        if study_version >= STUDY_VERSION_8_4:
            del optimization["include-split-exported-mps"]
        if study_version >= STUDY_VERSION_8_5:
            adequacy = types["adequacy patch"]
            adequacy["price-taking-order"] = str
            adequacy["include-hurdle-cost-csr"] = bool
            adequacy["check-csr-cost-function"] = bool
            adequacy["threshold-initiate-curtailment-sharing-rule"] = float
            adequacy["threshold-display-local-matching-rule-violations"] = float
            adequacy["threshold-csr-variable-bounds-relaxation"] = int

        if study_version >= STUDY_VERSION_8_6:
            types["adequacy patch"]["enable-first-step "] = bool

        if study_version >= STUDY_VERSION_9_2:
            adequacy = types["adequacy patch"]
            del adequacy["set-to-null-ntc-between-physical-out-for-first-step"]
            del adequacy["enable-first-step"]
            del other_preferences["initial-reservoir-levels"]
            types["compatibility"] = {"hydro-pmax": str}

        IniFileNode.__init__(
            self,
            context,
            config,
            types=types,
            reader=IniReader(DUPLICATE_KEYS),
            writer=IniWriter(special_keys=DUPLICATE_KEYS),
        )
