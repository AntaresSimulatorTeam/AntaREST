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

from typing import TypeVar, cast, overload

from antarest.study.business.model.scenario_builder_model import (
    RANDOM,
    AreaItemsScenarios,
    AreaScenarios,
    HydroLevelsScenarios,
    LinkScenarios,
    RandType,
    Ruleset,
    Rulesets,
    RulesetsUpdate,
    RulesetUpdate,
    ScenarioType,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

RuleValue = int | float | RandType | None
RulesetFileData = dict[str, RuleValue]
RulesetsFileData = dict[str, RulesetFileData]

_HYDRO_LEVEL_PERCENT = 100

_SCENARIO_TYPE_SYMBOLS = {
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

_SCENARIO_TYPE_FOR_SYMBOL = {v: k for k, v in _SCENARIO_TYPE_SYMBOLS.items()}


def _serialize_common(section: dict[str, RuleValue], scenario_type: ScenarioType, data: AreaScenarios) -> None:
    symbol = _SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            section[f"{symbol},{area},{year}"] = value


def _serialize_hydro_levels(
    section: dict[str, RuleValue], scenario_type: ScenarioType, data: HydroLevelsScenarios
) -> None:
    symbol = _SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, scenario_area in data.items():
        for year, value in scenario_area.items():
            val = value
            if isinstance(val, (int, float)) and val != float("nan"):
                val /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = val


def _serialize_links(section: dict[str, RuleValue], scenario_type: ScenarioType, data: LinkScenarios) -> None:
    symbol = _SCENARIO_TYPE_SYMBOLS[scenario_type]
    for link, scenario_link in data.items():
        for year, value in scenario_link.items():
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _serialize_clusters(section: dict[str, RuleValue], scenario_type: ScenarioType, data: AreaItemsScenarios) -> None:
    symbol = _SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, scenario_area in data.items():
        for cluster, scenario_area_cluster in scenario_area.items():
            for year, value in scenario_area_cluster.items():
                section[f"{symbol},{area},{year},{cluster}"] = value


def serialize_ruleset(ruleset: Ruleset) -> dict[str, RuleValue]:
    section: dict[str, RuleValue] = {}
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

    return dict(sorted(section.items()))


def serialize_rulesets(rulesets: Rulesets) -> RulesetsFileData:
    sections = {}
    for ruleset_name, ruleset in rulesets.items():
        sections[ruleset_name] = serialize_ruleset(ruleset)
    return sections


T = TypeVar("T")


def _check_not_none(value: T | None) -> T:
    if value is None:
        raise AssertionError("Value cannot be None")
    return value


def _add_value_simple(values: AreaScenarios, key: str, year: str, value: RuleValue) -> None:
    if value is None:
        value = RANDOM
    values.setdefault(key, {})[year] = value


def _add_value_double(values: AreaItemsScenarios, key1: str, key2: str, year: str, value: RuleValue) -> None:
    if values is None:
        raise ValueError("Scenario mapping should be initialized.")
    if value is None:
        value = RANDOM
    values.setdefault(key1, {}).setdefault(key2, {})[year] = value


def _to_percent(value: RuleValue) -> RuleValue:
    if isinstance(value, (int, float)):
        return int(100 * value)
    return value


@overload
def _parse_ruleset(ruleset_data: RulesetFileData, cls: type[Ruleset]) -> Ruleset: ...
@overload
def _parse_ruleset(ruleset_data: RulesetFileData, cls: type[RulesetUpdate]) -> RulesetUpdate: ...


def _parse_ruleset(ruleset_data: RulesetFileData, cls: type[Ruleset] | type[RulesetUpdate]) -> Ruleset | RulesetUpdate:
    """
    Parses rules data as read from INI file format, and populates a Ruleset or RulesetUpdate object with it.
    """
    ruleset = cls()
    for key, value in ruleset_data.items():
        symbol, *parts = key.split(",")
        scenario_type = _SCENARIO_TYPE_FOR_SYMBOL[symbol]
        if ruleset.get(scenario_type) is None:
            ruleset.set(scenario_type, {})
        match scenario_type:
            case ScenarioType.LOAD:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.load), area_id, year, value)
            case ScenarioType.THERMAL:
                area_id, year, cluster_id = parts
                _add_value_double(_check_not_none(ruleset.thermal), area_id, cluster_id, year, value)
            case ScenarioType.HYDRO:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.hydro), area_id, year, value)
            case ScenarioType.HYDRO_INITIAL_LEVEL:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.hydro_initial_levels), area_id, year, _to_percent(value))
            case ScenarioType.HYDRO_FINAL_LEVEL:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.hydro_final_levels), area_id, year, _to_percent(value))
            case ScenarioType.HYDRO_GENERATION_POWER:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.hydro_generation_power), area_id, year, value)
            case ScenarioType.LINK:
                area1, area2, year = parts
                _add_value_simple(_check_not_none(ruleset.ntc), f"{area1} / {area2}", year, value)
            case ScenarioType.SOLAR:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.solar), area_id, year, value)
            case ScenarioType.WIND:
                area_id, year = parts
                _add_value_simple(_check_not_none(ruleset.wind), area_id, year, value)
            case ScenarioType.RENEWABLE:
                area_id, year, cluster_id = parts
                _add_value_double(_check_not_none(ruleset.renewable), area_id, cluster_id, year, value)
            case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
                area_id, year, storage_id = parts
                _add_value_double(_check_not_none(ruleset.storage_inflows), area_id, storage_id, year, value)
            case ScenarioType.BINDING_CONSTRAINTS:
                group_id, year = parts
                _add_value_simple(_check_not_none(ruleset.binding_constraints), group_id, year, value)
            case _:
                raise NotImplementedError(f"Unknown symbol {symbol}")
    return ruleset


def parse_ruleset(ruleset_data: RulesetFileData) -> Ruleset:
    return _parse_ruleset(ruleset_data, cls=Ruleset)


def parse_ruleset_update(ruleset_data: RulesetFileData) -> RulesetUpdate:
    return _parse_ruleset(ruleset_data, cls=RulesetUpdate)


def parse_rulesets(rulesets_data: RulesetsFileData) -> Rulesets:
    rulesets: Rulesets = {}
    for ruleset_name, data in rulesets_data.items():
        rulesets[ruleset_name] = parse_ruleset(data)
    return rulesets


def parse_rulesets_update(rulesets_data: RulesetsFileData) -> RulesetsUpdate:
    rulesets: RulesetsUpdate = {}
    for ruleset_name, data in rulesets_data.items():
        rulesets[ruleset_name] = parse_ruleset_update(data)
    return rulesets


def extract_ruleset_data(
    file_study: FileStudy,
    ruleset_name: str,
    scenario_type: ScenarioType,
) -> RulesetFileData:
    """
    Extracts from file study only the relevant data for the provided ruleset name and scenario type.
    """
    try:
        suffix = _SCENARIO_TYPE_SYMBOLS[scenario_type]
        url = ["settings", "scenariobuilder", ruleset_name, suffix]
        return cast(RulesetFileData, file_study.tree.get(url))
    except KeyError:
        return {}
