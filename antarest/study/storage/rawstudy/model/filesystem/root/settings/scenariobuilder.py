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

import re
from typing import Dict, List, MutableMapping, Type

import typing_extensions as te
from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

_TSNumber: te.TypeAlias = int
_HydroLevel: te.TypeAlias = float
_Rules = MutableMapping[str, Type[_TSNumber] | Type[_HydroLevel]]


class ScenarioBuilder(IniFileNode):
    """
    Node representing the `settings/scenariobuilder.dat` file in an Antares study.
    This ".dat" file is a kind of ".ini"" file, where sections are rulesets.
    Each ruleset is a set of rules defined for each kind of generator or link.

    | Label                  | Symbol | Format                                     | Availability |
    |------------------------|:------:|--------------------------------------------|:------------:|
    | load                   |   l    | `l,<area>,<year> = <TS number>`            |              |
    | hydro                  |   h    | `h,<area>,<year> = <TS number>`            |              |
    | wind                   |   w    | `w,<area>,<year> = <TS number>`            |              |
    | solar                  |   s    | `s,<area>,<year> = <TS number>`            |              |
    | NTC (links)            |  ntc   | `ntc,<area1>,<area2>,<year> = <TS number>` |              |
    | thermal                |   t    | `t,<area>,<year>,<cluster> = <TS number>`  |              |
    | renewable              |   r    | `r,<area>,<year>,<cluster> = <TS number>`  |     8.1      |
    | binding-constraints    |   bc   | `bc,<group>,<year> = <TS number>`          |     8.7      |
    | hydro initial levels   |   hl   | `hl,<area>,<year> = <Level>`               |     8.0      |
    | hydro final levels     |  hfl   | `hfl,<area>,<year> = <Level>`              |     9.2      |
    | hydro generation power |  hgp   | `hgp,<area>,<year> = <TS number>`          |     9.1      |
    | short term storage     |  sts   | `sts,<area>,<year>,<cluster> = <TS number>`|     9.3      |

    Legend:
    - `<area>`: The area ID (in lower case).
    - `<area1>`, `<area2>`: The area IDs of the two connected areas (source and target).
    - `<year>`: The year (0-based index) of the time series.
    - `<cluster>`: The ID of the thermal / renewable cluster (in lower case).
    - `<group>`: The ID of the binding constraint group (in lower case).
    - `<TS number>`: The time series number (1-based index of the matrix column).
    - `<Level>`: The level of the hydraulic reservoir (in range 0-1).
    """

    def __init__(self, config: FileStudyTreeConfig):
        self.config = config
        super().__init__(
            config=config,
        )

    @override
    def _get_filtering_kwargs(self, url: List[str]) -> Dict[str, str]:
        # If the URL contains 2 elements, we can filter the options based on the type.
        if len(url) == 2:
            section, symbol = url
            if re.fullmatch(r"\w+", symbol):
                # Mutate the URL to get all values matching the generator type.
                url[:] = [section]
                return {"section": section, "option_regex": f"{symbol},.*"}

        return super()._get_filtering_kwargs(url)
