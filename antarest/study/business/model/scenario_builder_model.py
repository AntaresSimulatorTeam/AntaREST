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


import enum
from typing import Iterable, Literal, Mapping, TypeAlias, cast

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.study_index import StudyIndex


class ScenarioType(enum.StrEnum):
    """
    Scenario type

    - LOAD: Load scenario
    - THERMAL: Thermal cluster scenario
    - HYDRO: Hydraulic scenario
    - WIND: Wind scenario
    - SOLAR: Solar scenario
    - NTC: NTC scenario (link)
    - RENEWABLE: Renewable scenario
    - BINDING_CONSTRAINTS: Binding constraints scenario
    - HYDRO_INITIAL_LEVEL: hydraulic Initial level scenario
    - HYDRO_FINAL_LEVEL: hydraulic Final level scenario
    - HYDRO_GENERATION_POWER: hydraulic Generation power scenario
    - SHORT_TERM_STORAGE_INFLOWS: Short term storage inflows scenario
    """

    LOAD = "load"
    THERMAL = "thermal"
    HYDRO = "hydro"
    WIND = "wind"
    SOLAR = "solar"
    LINK = "ntc"
    RENEWABLE = "renewable"
    BINDING_CONSTRAINTS = "bindingConstraints"
    HYDRO_INITIAL_LEVEL = "hydroInitialLevels"
    HYDRO_FINAL_LEVEL = "hydroFinalLevels"
    HYDRO_GENERATION_POWER = "hydroGenerationPower"
    SHORT_TERM_STORAGE_INFLOWS = "shortTermStorageInflows"


# Random is represented as ""
RandType: TypeAlias = Literal[""]
Value: TypeAlias = float | int | RandType

AreaId: TypeAlias = str
LinkId: TypeAlias = str
BcGroupId: TypeAlias = str
ItemId: TypeAlias = str

McYearToTimeSeries: TypeAlias = dict[str, Value]
McYearToValue: TypeAlias = dict[str, Value]

AreaScenarios: TypeAlias = dict[AreaId, McYearToTimeSeries]
LinkScenarios: TypeAlias = dict[LinkId, McYearToTimeSeries]
BcGroupScenarios: TypeAlias = dict[BcGroupId, McYearToTimeSeries]
AreaItemsScenarios: TypeAlias = dict[AreaId, dict[ItemId, McYearToTimeSeries]]
HydroLevelsScenarios: TypeAlias = dict[AreaId, McYearToValue]

AnyScenarios: TypeAlias = AreaScenarios | AreaItemsScenarios | LinkScenarios | HydroLevelsScenarios

_OneLevelScenarios = dict[str, McYearToTimeSeries]
_TwoLevelScenarios = dict[str, dict[str, McYearToTimeSeries]]

# The unique instance of RandType
RANDOM: RandType = ""


class Ruleset(AntaresBaseModel, populate_by_name=True, extra="forbid"):
    """
    A ruleset defines, for each item in the study, a mapping of MC year to the data to be used.

    In the vast majority of cases, the data is simply a timeseries number to be used,
    but for specific cases it can be an actual value, like the level of an hydro reservoir.
    """

    load: AreaScenarios = Field(default_factory=dict)
    thermal: AreaItemsScenarios = Field(default_factory=dict)
    hydro: AreaScenarios = Field(default_factory=dict)
    hydro_initial_levels: HydroLevelsScenarios = Field(default_factory=dict)
    hydro_final_levels: HydroLevelsScenarios = Field(default_factory=dict)
    hydro_generation_power: AreaScenarios = Field(default_factory=dict)
    wind: AreaScenarios = Field(default_factory=dict)
    solar: AreaScenarios = Field(default_factory=dict)
    ntc: LinkScenarios = Field(default_factory=dict)
    renewable: AreaItemsScenarios = Field(default_factory=dict)
    binding_constraints: BcGroupScenarios = Field(default_factory=dict)
    storage_inflows: AreaItemsScenarios = Field(default_factory=dict)

    def get(self, scenario_type: ScenarioType) -> AnyScenarios:
        res = _get_by_type(self, scenario_type)
        if res is None:
            raise ValueError("Should not have a None scenario mapping in Ruleset")
        return res

    def set(self, scenario_type: ScenarioType, scenarios: AnyScenarios) -> None:
        _set_by_type(self, scenario_type, scenarios)


Rulesets: TypeAlias = dict[str, Ruleset]


class RulesetUpdate(AntaresBaseModel, populate_by_name=True, extra="forbid"):
    """
    An update to a Ruleset object.
    """

    load: AreaScenarios | None = None
    thermal: AreaItemsScenarios | None = None
    hydro: AreaScenarios | None = None
    hydro_initial_levels: HydroLevelsScenarios | None = None
    hydro_final_levels: HydroLevelsScenarios | None = None
    hydro_generation_power: AreaScenarios | None = None
    wind: AreaScenarios | None = None
    solar: AreaScenarios | None = None
    ntc: LinkScenarios | None = None
    renewable: AreaItemsScenarios | None = None
    binding_constraints: BcGroupScenarios | None = None
    storage_inflows: AreaItemsScenarios | None = None

    def get(self, scenario_type: ScenarioType) -> AnyScenarios | None:
        return _get_by_type(self, scenario_type)

    def set(self, scenario_type: ScenarioType, scenarios: AnyScenarios | None) -> None:
        _set_by_type(self, scenario_type, scenarios)


def _get_by_type(self: Ruleset | RulesetUpdate, scenario_type: ScenarioType) -> AnyScenarios | None:
    match scenario_type:
        case ScenarioType.LOAD:
            return self.load
        case ScenarioType.THERMAL:
            return self.thermal
        case ScenarioType.HYDRO:
            return self.hydro
        case ScenarioType.HYDRO_INITIAL_LEVEL:
            return self.hydro_initial_levels
        case ScenarioType.HYDRO_FINAL_LEVEL:
            return self.hydro_final_levels
        case ScenarioType.HYDRO_GENERATION_POWER:
            return self.hydro_generation_power
        case ScenarioType.SOLAR:
            return self.solar
        case ScenarioType.WIND:
            return self.wind
        case ScenarioType.RENEWABLE:
            return self.renewable
        case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
            return self.storage_inflows
        case ScenarioType.BINDING_CONSTRAINTS:
            return self.binding_constraints
        case ScenarioType.LINK:
            return self.ntc
        case _:
            raise ValueError(f"Unknown scenario type {scenario_type}")


def _set_by_type(self: Ruleset | RulesetUpdate, scenario_type: ScenarioType, scenarios: AnyScenarios | None) -> None:
    match scenario_type:
        case ScenarioType.LOAD:
            self.load = cast(AreaScenarios, scenarios)
        case ScenarioType.THERMAL:
            self.thermal = cast(AreaItemsScenarios, scenarios)
        case ScenarioType.HYDRO:
            self.hydro = cast(AreaScenarios, scenarios)
        case ScenarioType.HYDRO_INITIAL_LEVEL:
            self.hydro_initial_levels = cast(AreaScenarios, scenarios)
        case ScenarioType.HYDRO_FINAL_LEVEL:
            self.hydro_final_levels = cast(AreaScenarios, scenarios)
        case ScenarioType.HYDRO_GENERATION_POWER:
            self.hydro_generation_power = cast(AreaScenarios, scenarios)
        case ScenarioType.SOLAR:
            self.solar = cast(AreaScenarios, scenarios)
        case ScenarioType.WIND:
            self.wind = cast(AreaScenarios, scenarios)
        case ScenarioType.RENEWABLE:
            self.renewable = cast(AreaItemsScenarios, scenarios)
        case ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
            self.storage_inflows = cast(AreaItemsScenarios, scenarios)
        case ScenarioType.BINDING_CONSTRAINTS:
            self.binding_constraints = cast(AreaScenarios, scenarios)
        case ScenarioType.LINK:
            self.ntc = cast(AreaScenarios, scenarios)
        case _:
            raise ValueError(f"Unknown scenario type {scenario_type}")


RulesetsUpdate: TypeAlias = dict[str, RulesetUpdate]


def _create_scenarios_mapping(names: Iterable[str], years: list[str]) -> AreaScenarios:
    return {n: dict.fromkeys(years, RANDOM) for n in names}


def _create_cluster_scenarios_mapping(names: Mapping[str, Iterable[str]], years: list[str]) -> AreaItemsScenarios:
    return {n: _create_scenarios_mapping(cluster_names, years) for n, cluster_names in names.items()}


def initialize_ruleset(years: list[str], index: StudyIndex, scenario_types: set[ScenarioType] | None = None) -> Ruleset:
    """
    Creates a ruleset initialized with random ("") for all items and years of a study.

    Optionally, you may choose to initialize only certain scenario types.
    """
    if scenario_types is None:
        scenario_types = set(ScenarioType)

    return Ruleset(
        load=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.LOAD in scenario_types
        else {},
        thermal=_create_cluster_scenarios_mapping(names=index.thermal_ids, years=years)
        if ScenarioType.THERMAL in scenario_types
        else {},
        hydro=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO in scenario_types
        else {},
        hydro_initial_levels=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_INITIAL_LEVEL in scenario_types
        else {},
        hydro_final_levels=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_FINAL_LEVEL in scenario_types
        else {},
        hydro_generation_power=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_GENERATION_POWER in scenario_types
        else {},
        solar=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.SOLAR in scenario_types
        else {},
        wind=_create_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.WIND in scenario_types
        else {},
        renewable=_create_cluster_scenarios_mapping(names=index.renewable_ids, years=years)
        if ScenarioType.RENEWABLE in scenario_types
        else {},
        storage_inflows=_create_cluster_scenarios_mapping(names=index.storage_ids, years=years)
        if ScenarioType.SHORT_TERM_STORAGE_INFLOWS in scenario_types
        else {},
        binding_constraints=_create_scenarios_mapping(names=index.bc_group_ids, years=years)
        if ScenarioType.BINDING_CONSTRAINTS in scenario_types
        else {},
        ntc=_create_scenarios_mapping(names=index.link_ids, years=years) if ScenarioType.LINK in scenario_types else {},
    )


def _update_mapping(base: McYearToTimeSeries, update: McYearToTimeSeries | None) -> None:
    if update is None:
        return
    base.update(update)


def _update_simple_mapping(base: _OneLevelScenarios, update: _OneLevelScenarios | None) -> None:
    if update is None:
        return
    for name, mapping in update.items():
        _update_mapping(base.setdefault(name, {}), mapping)


def _update_double_mapping(base: _TwoLevelScenarios, update: _TwoLevelScenarios | None) -> None:
    if update is None:
        return
    for name, mapping in update.items():
        _update_simple_mapping(base.setdefault(name, {}), mapping)


def update_ruleset(base: Ruleset, update: RulesetUpdate) -> None:
    _update_simple_mapping(base.load, update.load)
    _update_double_mapping(base.thermal, update.thermal)
    _update_simple_mapping(base.hydro, update.hydro)
    _update_simple_mapping(base.hydro_initial_levels, update.hydro_initial_levels)
    _update_simple_mapping(base.hydro_final_levels, update.hydro_final_levels)
    _update_simple_mapping(base.hydro_generation_power, update.hydro_generation_power)
    _update_simple_mapping(base.solar, update.solar)
    _update_simple_mapping(base.wind, update.wind)
    _update_simple_mapping(base.binding_constraints, update.binding_constraints)
    _update_double_mapping(base.renewable, update.renewable)
    _update_double_mapping(base.storage_inflows, update.storage_inflows)
    _update_simple_mapping(base.ntc, update.ntc)


def update_rulesets(base: Rulesets, update: RulesetsUpdate) -> None:
    lower_case_base = {k.lower(): v for k, v in base.items()}
    for name, ruleset_update in update.items():
        if name.lower() not in lower_case_base:
            ruleset = Ruleset()
            update_ruleset(ruleset, ruleset_update)
            base[name] = ruleset
        else:
            update_ruleset(lower_case_base[name.lower()], ruleset_update)
