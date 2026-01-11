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

"""
Serialization and parsing for scenariobuilder.dat file
"""

from typing import Any, TypeVar, cast, overload

from antares.study.version import StudyVersion

from antarest.core.utils.dict_utils import iter_nested, iter_nested_2, iter_nested_3
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
    StorageConstraintsScenarios,
    validate_ruleset_against_version,
)

RuleValue = int | float | RandType | None
RulesetFileData = dict[str, RuleValue]
RulesetsFileData = dict[str, RulesetFileData]

_HYDRO_LEVEL_PERCENT = 100

SCENARIO_TYPE_SYMBOLS = {
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
    ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS: "sta",
}

_SCENARIO_TYPE_FOR_SYMBOL = {v: k for k, v in SCENARIO_TYPE_SYMBOLS.items()}


def _should_write(value: RuleValue) -> bool:
    """
    "random" values must not be written to INI file.
    """
    return value is not None and value != RANDOM


def _serialize_common(section: dict[str, RuleValue], scenario_type: ScenarioType, data: AreaScenarios) -> None:
    symbol = SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, year, value in iter_nested(data):
        if _should_write(value):
            section[f"{symbol},{area},{year}"] = value


def _serialize_hydro_levels(
    section: dict[str, RuleValue], scenario_type: ScenarioType, data: HydroLevelsScenarios
) -> None:
    symbol = SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, year, value in iter_nested(data):
        if _should_write(value):
            val = value
            if isinstance(val, (int, float)) and val != float("nan"):
                val /= _HYDRO_LEVEL_PERCENT
            section[f"{symbol},{area},{year}"] = val


def _serialize_links(section: dict[str, RuleValue], scenario_type: ScenarioType, data: LinkScenarios) -> None:
    symbol = SCENARIO_TYPE_SYMBOLS[scenario_type]
    for link, year, value in iter_nested(data):
        if _should_write(value):
            area1, area2 = link.split(" / ")
            section[f"{symbol},{area1},{area2},{year}"] = value


def _serialize_clusters(section: dict[str, RuleValue], scenario_type: ScenarioType, data: AreaItemsScenarios) -> None:
    symbol = SCENARIO_TYPE_SYMBOLS[scenario_type]
    for area, cluster, year, value in iter_nested_2(data):
        if _should_write(value):
            section[f"{symbol},{area},{year},{cluster}"] = value


def _serialize_sts_constraints(section: dict[str, RuleValue], data: StorageConstraintsScenarios) -> None:
    symbol = SCENARIO_TYPE_SYMBOLS[ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS]
    for area, storage, constraint, year, value in iter_nested_3(data):
        if _should_write(value):
            section[f"{symbol},{area},{year},{storage},{constraint}"] = value


def serialize_ruleset(ruleset: Ruleset, version: StudyVersion) -> dict[str, RuleValue]:
    section: dict[str, RuleValue] = {}
    validate_ruleset_against_version(version, ruleset)
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
    _serialize_sts_constraints(section, ruleset.storage_constraints)

    return dict(sorted(section.items()))


def serialize_rulesets(rulesets: Rulesets, version: StudyVersion) -> RulesetsFileData:
    sections = {}
    for ruleset_name, ruleset in rulesets.items():
        sections[ruleset_name] = serialize_ruleset(ruleset, version)
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
    if value is None:
        value = RANDOM
    values.setdefault(key1, {}).setdefault(key2, {})[year] = value


def _add_value_triple(
    values: StorageConstraintsScenarios, key1: str, key2: str, key3: str, year: str, value: RuleValue
) -> None:
    if value is None:
        value = RANDOM
    values.setdefault(key1, {}).setdefault(key2, {}).setdefault(key3, {})[year] = value


def _to_percent(value: RuleValue) -> RuleValue:
    if isinstance(value, (int, float)):
        return 100 * value
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
            case ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
                area, year, storage, constraint = parts
                _add_value_triple(_check_not_none(ruleset.storage_constraints), area, storage, constraint, year, value)
            case _:
                raise NotImplementedError(f"Unknown symbol {symbol}")
    return ruleset


def parse_ruleset(ruleset_data: RulesetFileData) -> Ruleset:
    return _parse_ruleset(ruleset_data, cls=Ruleset)


def parse_ruleset_update(ruleset_data: RulesetFileData) -> RulesetUpdate:
    return _parse_ruleset(ruleset_data, cls=RulesetUpdate)


def parse_rulesets_from_any(data: Any, version: StudyVersion) -> Rulesets:
    rulesets_data = cast(RulesetsFileData, data)
    return parse_rulesets(rulesets_data, version)


def parse_rulesets(rulesets_data: RulesetsFileData, version: StudyVersion) -> Rulesets:
    rulesets: Rulesets = {}
    for ruleset_name, data in rulesets_data.items():
        ruleset = parse_ruleset(data)
        validate_ruleset_against_version(version, ruleset)
        rulesets[ruleset_name] = ruleset
    return rulesets


def parse_rulesets_update(rulesets_data: RulesetsFileData) -> RulesetsUpdate:
    rulesets: RulesetsUpdate = {}
    for ruleset_name, data in rulesets_data.items():
        rulesets[ruleset_name] = parse_ruleset_update(data)
    return rulesets
