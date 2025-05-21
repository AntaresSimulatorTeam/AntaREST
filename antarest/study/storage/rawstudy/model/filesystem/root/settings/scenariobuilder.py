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

import re
from typing import Dict, List, MutableMapping, Type

import typing_extensions as te
from typing_extensions import override

from antarest.study.model import (
    STUDY_VERSION_8,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_7,
    STUDY_VERSION_9_1,
    STUDY_VERSION_9_2,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling, FileStudyTreeConfig
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

        rules: _Rules = {}
        self._populate_load_hydro_wind_solar_rules(rules)
        self._populate_ntc_rules(rules)
        self._populate_thermal_rules(rules)

        # Rules are defined for a specific version of the study.
        study_version = config.version
        if study_version >= STUDY_VERSION_8_1 and EnrModelling(self.config.enr_modelling) == EnrModelling.CLUSTERS:
            self._populate_renewable_rules(rules)
        if study_version >= STUDY_VERSION_8_7:
            self._populate_binding_constraints_rules(rules)
        if study_version >= STUDY_VERSION_8:
            self._populate_hydro_initial_level_rules(rules)
        if study_version >= STUDY_VERSION_9_2:
            self._populate_hydro_final_level_rules(rules)
        if study_version >= STUDY_VERSION_9_1:
            self._populate_hydro_generation_power_rules(rules)

        super().__init__(
            config=config,
            types={"Default Ruleset": rules},
        )

    def _populate_load_hydro_wind_solar_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            for symbol in ("l", "h", "w", "s"):
                rules[f"{symbol},{area_id},0"] = _TSNumber

    def _populate_ntc_rules(self, rules: _Rules) -> None:
        for area1_id in self.config.areas:
            for area2_id in self.config.get_links(area1_id):
                rules[f"ntc,{area1_id},{area2_id},0"] = _TSNumber

    def _populate_thermal_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            for cl_id in (th.lower() for th in self.config.get_thermal_ids(area_id)):
                rules[f"t,{area_id},0,{cl_id}"] = _TSNumber

    def _populate_renewable_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            for cl_id in (renew.lower() for renew in self.config.get_renewable_ids(area_id)):
                rules[f"r,{area_id},0,{cl_id}"] = _TSNumber

    def _populate_binding_constraints_rules(self, rules: _Rules) -> None:
        for group_id in (gr.lower() for gr in self.config.get_binding_constraint_groups()):
            rules[f"bc,{group_id},0"] = _TSNumber

    def _populate_hydro_initial_level_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            rules[f"hl,{area_id},0"] = _HydroLevel

    def _populate_hydro_final_level_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            rules[f"hfl,{area_id},0"] = _HydroLevel

    def _populate_hydro_generation_power_rules(self, rules: _Rules) -> None:
        for area_id in self.config.areas:
            rules[f"hgp,{area_id},0"] = _TSNumber

    @override
    def _get_filtering_kwargs(self, url: List[str]) -> Dict[str, str]:
        # If the URL contains 2 elements, we can filter the options based on the generator type.
        if len(url) == 2:
            section, symbol = url
            if re.fullmatch(r"\w+", symbol):
                # Mutate the URL to get all values matching the generator type.
                url[:] = [section]
                return {"section": section, "option_regex": f"{symbol},.*"}

        # If the URL contains 3 elements, we can filter on the generator type and area (or group for BC).
        elif len(url) == 3:
            section, symbol, area = url
            if re.fullmatch(r"\w+", symbol):
                # Mutate the URL to get all values matching the generator type.
                url[:] = [section]
                area_re = re.escape(area)
                return {"section": section, "option_regex": f"{symbol},{area_re},.*"}

        # If the URL contains 4 elements, we can filter on the generator type, area, and cluster.
        elif len(url) == 4:
            section, symbol, area, cluster = url
            if re.fullmatch(r"\w+", symbol):
                # Mutate the URL to get all values matching the generator type.
                url[:] = [section]
                if symbol in ("t", "r"):
                    area_re = re.escape(area)
                    cluster_re = re.escape(cluster)
                    return {"section": section, "option_regex": rf"{symbol},{area_re},\d+,{cluster_re}"}
                elif symbol == "ntc":
                    area1_re = re.escape(area)
                    area2_re = re.escape(cluster)
                    return {"section": section, "option_regex": f"{symbol},{area1_re},{area2_re},.*"}

        return super()._get_filtering_kwargs(url)
