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

"""
Serialization and parsing for scenariobuilder.dat file
"""

from typing import TypeAlias

from pydantic import TypeAdapter

from antarest.study.business.model.scenario_builder_model import (
    RANDOM,
    AreaItemsScenarios,
    AreaScenarios,
    HydroLevelsScenarios,
    RandType,
    Ruleset,
    Rulesets,
    ScenarioType,
)
from antarest.study.business.scenario_builder_management import SYMBOLS_BY_SCENARIO_TYPES

RulesetSection: TypeAlias = dict[str, int | float | RandType]  # TODO: float allowed or not ?
RulesetSections: TypeAlias = dict[str, RulesetSection]

_RULESETS_ADAPTER: TypeAdapter[Rulesets] = TypeAdapter(Rulesets)

# Symbols used in scenario builder data
_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "bc", "hgp"
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r", "sts"

_HYDRO_LEVEL_PERCENT = 100

SYMBOLS_BY_SCENARIO_TYPES = {
    ScenarioType.LOAD: "l",
    ScenarioType.HYDRO: "h",
    ScenarioType.WIND: "w",
    ScenarioType.SOLAR: "s",
    ScenarioType.THERMAL: "t",
    ScenarioType.RENEWABLE: "r",
    ScenarioType.LINK: "ntc",
    ScenarioType.BINDING_CONSTRAINTS: "bc",
    ScenarioType.HYDRO_INITIAL_LEVEL: "hl",
    ScenarioType.HYDRO_FINAL_LEVEL: "hfl",
    ScenarioType.HYDRO_GENERATION_POWER: "hgp",
    ScenarioType.SHORT_TERM_STORAGE_INFLOWS: "sts",
}

SCENARIO_TYPE_BY_SYMBOL = {v: k for k, v in SYMBOLS_BY_SCENARIO_TYPES.items()}


def _serialize_common(section: RulesetSection, scenario_type: ScenarioType, data: AreaScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            section[f"{symbol},{area},{year}"] = value


def _serialize_hydro_levels(
    section: RulesetSection, scenario_type: ScenarioType, data: HydroLevelsScenarios | None
) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            val = value
            if isinstance(value, (int, float)) and value != float("nan"):
                val /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = val


def _serialize_links(section: RulesetSection, scenario_type: ScenarioType, data: AreaScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for link, scenario_link in data.items():
        for year, value in scenario_link.items():
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _serialize_clusters(section: RulesetSection, scenario_type: ScenarioType, data: AreaItemsScenarios | None) -> None:
    if not data:
        return
    symbol = SYMBOLS_BY_SCENARIO_TYPES[scenario_type]
    for area, scenario_area in data.items():
        for cluster, scenario_area_cluster in scenario_area.items():
            for year, value in scenario_area_cluster.items():
                section[f"{symbol},{area},{year},{cluster}"] = value


def serialize_rulesets(rulesets: Rulesets) -> RulesetSections:
    sections: RulesetSections = {}
    for ruleset_name, ruleset in rulesets.items():
        section = sections[ruleset_name] = {}
        _serialize_common(section, ScenarioType.LOAD, ruleset.load)
        _serialize_clusters(section, ScenarioType.THERMAL, ruleset.thermal)
        _serialize_common(section, ScenarioType.HYDRO, ruleset.hydro)
        _serialize_hydro_levels(section, ScenarioType.HYDRO_INITIAL_LEVEL, ruleset.hydro_initial_levels)
        _serialize_hydro_levels(section, ScenarioType.HYDRO_FINAL_LEVEL, ruleset.hydro_final_levels)
        _serialize_common(section, ScenarioType.HYDRO_GENERATION_POWER, ruleset.hydro_generation_power)
        _serialize_common(section, ScenarioType.WIND, ruleset.wind)
        _serialize_common(section, ScenarioType.SOLAR, ruleset.solar)
        _serialize_links(section, ScenarioType.LINK, ruleset.ntc)
        _serialize_clusters(section, ScenarioType.RENEWABLE, ruleset.renewable)
        _serialize_common(section, ScenarioType.BINDING_CONSTRAINTS, ruleset.binding_constraints)
        _serialize_clusters(section, ScenarioType.SHORT_TERM_STORAGE_INFLOWS, ruleset.storage_inflows)
    return sections


def _add_value_simple(values: AreaScenarios, key: str, year: str, value: int | float) -> None:
    values.setdefault(key, {})[year] = value


def _add_value_double(values: AreaItemsScenarios, key1: str, key2: str, year: str, value: int | float) -> None:
    values.setdefault(key1, {}).setdefault(key2, {})[year] = value


def parse_ruleset(ruleset_data: RulesetSection, ruleset: Ruleset | None = None) -> Ruleset:
    """
    Parses rules data as read from INI file, and populates a Ruleset object with it.

    A pre-existing Ruleset object can be provided, in which case it will be updated with the new data.
    Otherwise, a new one is created.
    """
    ruleset = ruleset or Ruleset()
    for key, value in ruleset_data.items():
        if value == RANDOM:
            continue
        symbol, *parts = key.split(",")
        scenario_type = SCENARIO_TYPE_BY_SYMBOL.get(symbol)
        match scenario_type:
            case ScenarioType.LOAD:
                area_id, year = parts
                _add_value_simple(ruleset.load, area_id, year, value)
            case ScenarioType.THERMAL:
                area_id, year, cluster_id = parts
                _add_value_double(ruleset.thermal, area_id, cluster_id, year, value)
            case ScenarioType.HYDRO:
                area_id, year = parts
                _add_value_simple(ruleset.hydro, area_id, year, value)
            case ScenarioType.HYDRO_INITIAL_LEVEL:
                area_id, year = parts
                _add_value_simple(ruleset.hydro_initial_levels, area_id, year, value * 100)
            case ScenarioType.HYDRO_FINAL_LEVEL:
                area_id, year = parts
                _add_value_simple(ruleset.hydro_final_levels, area_id, year, value * 100)
            case ScenarioType.HYDRO_GENERATION_POWER:
                area_id, year = parts
                _add_value_simple(ruleset.hydro_generation_power, area_id, year, value)
            case ScenarioType.LINK:
                area1, area2, year = parts
                _add_value_simple(ruleset.ntc, f"{area1} / {area2}", year, value)
            case ScenarioType.SOLAR:
                area_id, year = parts
                _add_value_simple(ruleset.solar, area_id, year, value)
            case ScenarioType.WIND:
                area_id, year = parts
                _add_value_simple(ruleset.wind, area_id, year, value)
            case ScenarioType.RENEWABLE:
                area_id, year, cluster_id = parts
                _add_value_double(ruleset.thermal, area_id, cluster_id, year, value)
            case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
                area_id, year, storage_id = parts
                _add_value_double(ruleset.thermal, area_id, storage_id, year, value)
            case ScenarioType.BINDING_CONSTRAINTS:
                group_id, year = parts
                _add_value_simple(ruleset.wind, group_id, year, value)
            case _:
                raise NotImplementedError(f"Unknown symbol {symbol}")
    return Ruleset.model_validate(ruleset)


def parse_rulesets(rulesets_data: RulesetSections) -> Rulesets:
    rulesets: Rulesets = {}
    for ruleset_name, data in rulesets_data.items():
        ruleset = rulesets.setdefault(ruleset_name, Ruleset())
        parse_ruleset(data, ruleset)
    return rulesets
