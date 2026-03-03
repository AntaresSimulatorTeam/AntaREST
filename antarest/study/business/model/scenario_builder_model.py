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


import enum
from typing import Any, Final, Iterable, Literal, Mapping, TypeAlias, cast

from antares.study.version import StudyVersion
from pydantic import Field

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.study_index import StudyIndex
from antarest.study.model import STUDY_VERSION_8_7, STUDY_VERSION_9_2, STUDY_VERSION_9_3

DEFAULT_RULESET_NAME: Final[str] = "Default Ruleset"


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
    SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS = "shortTermStorageAdditionalConstraints"


# Random is represented as ""
RandType: TypeAlias = Literal[""]
Value: TypeAlias = float | int | RandType

AreaId: TypeAlias = str
LinkId: TypeAlias = str
BcGroupId: TypeAlias = str
ItemId: TypeAlias = str
ConstraintId: TypeAlias = str

McYearToTimeSeries: TypeAlias = dict[str, Value]
McYearToValue: TypeAlias = dict[str, Value]

AreaScenarios: TypeAlias = dict[AreaId, McYearToTimeSeries]
LinkScenarios: TypeAlias = dict[LinkId, McYearToTimeSeries]
BcGroupScenarios: TypeAlias = dict[BcGroupId, McYearToTimeSeries]
AreaItemsScenarios: TypeAlias = dict[AreaId, dict[ItemId, McYearToTimeSeries]]
HydroLevelsScenarios: TypeAlias = dict[AreaId, McYearToValue]
StorageConstraintsScenarios: TypeAlias = dict[AreaId, dict[ItemId, dict[ConstraintId, McYearToTimeSeries]]]

AnyScenarios: TypeAlias = (
    AreaScenarios | AreaItemsScenarios | LinkScenarios | HydroLevelsScenarios | StorageConstraintsScenarios
)

_OneLevelScenarios = dict[str, McYearToTimeSeries]
_TwoLevelScenarios = dict[str, _OneLevelScenarios]
_ThreeLevelScenarios = dict[str, _TwoLevelScenarios]

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
    hydro_generation_power: AreaScenarios = Field(default_factory=dict)
    wind: AreaScenarios = Field(default_factory=dict)
    solar: AreaScenarios = Field(default_factory=dict)
    ntc: LinkScenarios = Field(default_factory=dict)
    renewable: AreaItemsScenarios = Field(default_factory=dict)
    # Introduced in v8.7
    binding_constraints: BcGroupScenarios = Field(default_factory=dict)
    # Introduced in v9.2
    hydro_final_levels: HydroLevelsScenarios = Field(default_factory=dict)
    # Introduced in v9.3
    storage_inflows: AreaItemsScenarios = Field(default_factory=dict)
    storage_constraints: StorageConstraintsScenarios = Field(default_factory=dict)

    def get(self, scenario_type: ScenarioType) -> AnyScenarios:
        res = _get_by_type(self, scenario_type)
        if res is None:
            raise ValueError("Should not have a None scenario mapping in Ruleset")
        return res

    def set(self, scenario_type: ScenarioType, scenarios: AnyScenarios) -> None:
        _set_by_type(self, scenario_type, scenarios)


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
    storage_constraints: StorageConstraintsScenarios | None = None

    def get(self, scenario_type: ScenarioType) -> AnyScenarios | None:
        return _get_by_type(self, scenario_type)

    def set(self, scenario_type: ScenarioType, scenarios: AnyScenarios) -> None:
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
        case ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
            return self.storage_constraints
        case _:
            raise ValueError(f"Unknown scenario type {scenario_type}")


def _set_by_type(self: Ruleset | RulesetUpdate, scenario_type: ScenarioType, scenarios: AnyScenarios) -> None:
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
        case ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
            self.storage_constraints = cast(StorageConstraintsScenarios, scenarios)
        case _:
            raise ValueError(f"Unknown scenario type {scenario_type}")


def _create_1_level_scenarios_mapping(names: Iterable[str], years: list[str]) -> _OneLevelScenarios:
    """
    Initializes a scenario mapping filled with random.
    """
    return {n: dict.fromkeys(years, RANDOM) for n in names}


def _create_2_levels_scenarios_mapping(names: Mapping[str, Iterable[str]], years: list[str]) -> _TwoLevelScenarios:
    """
    Initializes a scenario mapping filled with random.
    """
    return {n: _create_1_level_scenarios_mapping(item_names, years) for n, item_names in names.items()}


def _create_3_levels_scenarios_mapping(
    names: Mapping[str, Mapping[str, Iterable[str]]], years: list[str]
) -> _ThreeLevelScenarios:
    """
    Initializes a scenario mapping filled with random.
    """
    return {n: _create_2_levels_scenarios_mapping(item_names, years) for n, item_names in names.items()}


def _get_scenario_types_according_to_version(version: StudyVersion) -> set[ScenarioType]:
    all_scenario_types = set(ScenarioType)
    if version < STUDY_VERSION_8_7:
        all_scenario_types.remove(ScenarioType.BINDING_CONSTRAINTS)
    if version < STUDY_VERSION_9_2:
        all_scenario_types.remove(ScenarioType.HYDRO_FINAL_LEVEL)
    if version < STUDY_VERSION_9_3:
        all_scenario_types.remove(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
        all_scenario_types.remove(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    return all_scenario_types


def initialize_ruleset_with_version(
    years: list[str], index: StudyIndex, version: StudyVersion, scenario_types: set[ScenarioType] | None = None
) -> Ruleset:
    """
    Creates a ruleset initialized with random ("") for all items and years of a study.
    Only instantiate the rulesets if they existed in the given study version.

    Optionally, you may choose to initialize only certain scenario types.
    """
    acceptable_types = _get_scenario_types_according_to_version(version)
    if scenario_types is None:
        scenario_types = acceptable_types

    if invalid_types := scenario_types - acceptable_types:
        raise InvalidFieldForVersionError(
            f"Invalid scenario types {[e.value for e in invalid_types]} provided for version {version}"
        )

    return Ruleset(
        load=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.LOAD in scenario_types
        else {},
        thermal=_create_2_levels_scenarios_mapping(names=index.thermal_ids, years=years)
        if ScenarioType.THERMAL in scenario_types
        else {},
        hydro=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO in scenario_types
        else {},
        hydro_initial_levels=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_INITIAL_LEVEL in scenario_types
        else {},
        hydro_final_levels=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_FINAL_LEVEL in scenario_types
        else {},
        hydro_generation_power=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.HYDRO_GENERATION_POWER in scenario_types
        else {},
        solar=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.SOLAR in scenario_types
        else {},
        wind=_create_1_level_scenarios_mapping(names=index.area_ids, years=years)
        if ScenarioType.WIND in scenario_types
        else {},
        renewable=_create_2_levels_scenarios_mapping(names=index.renewable_ids, years=years)
        if ScenarioType.RENEWABLE in scenario_types
        else {},
        storage_inflows=_create_2_levels_scenarios_mapping(names=index.storage_ids, years=years)
        if ScenarioType.SHORT_TERM_STORAGE_INFLOWS in scenario_types
        else {},
        binding_constraints=_create_1_level_scenarios_mapping(names=index.bc_group_ids, years=years)
        if ScenarioType.BINDING_CONSTRAINTS in scenario_types
        else {},
        ntc=_create_1_level_scenarios_mapping(names=index.link_ids, years=years)
        if ScenarioType.LINK in scenario_types
        else {},
        storage_constraints=_create_3_levels_scenarios_mapping(names=index.sts_constraint_ids, years=years)
        if ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS in scenario_types
        else {},
    )


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field):  # The value should be an empty dict
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_ruleset_against_version(version: StudyVersion, ruleset: Ruleset | RulesetUpdate) -> None:
    if version < STUDY_VERSION_8_7:
        _check_min_version(ruleset, "binding_constraints", version)
    if version < STUDY_VERSION_9_2:
        _check_min_version(ruleset, "hydro_final_levels", version)
    if version < STUDY_VERSION_9_3:
        _check_min_version(ruleset, "storage_inflows", version)
        _check_min_version(ruleset, "storage_constraints", version)


def _update_mapping(base: McYearToTimeSeries, update: McYearToTimeSeries | None) -> None:
    if update is None:
        return
    base.update(update)


def _update_1_level_mapping(base: _OneLevelScenarios, update: _OneLevelScenarios | None) -> None:
    if update is None:
        return
    for name, mapping in update.items():
        _update_mapping(base.setdefault(name, {}), mapping)


def _update_2_levels_mapping(base: _TwoLevelScenarios, update: _TwoLevelScenarios | None) -> None:
    if update is None:
        return
    for name, mapping in update.items():
        _update_1_level_mapping(base.setdefault(name, {}), mapping)


def _update_3_levels_mapping(base: _ThreeLevelScenarios, update: _ThreeLevelScenarios | None) -> None:
    if update is None:
        return
    for name, mapping in update.items():
        _update_2_levels_mapping(base.setdefault(name, {}), mapping)


def update_ruleset(base: Ruleset, update: RulesetUpdate, version: StudyVersion) -> None:
    _update_1_level_mapping(base.load, update.load)
    _update_2_levels_mapping(base.thermal, update.thermal)
    _update_1_level_mapping(base.hydro, update.hydro)
    _update_1_level_mapping(base.hydro_initial_levels, update.hydro_initial_levels)
    _update_1_level_mapping(base.hydro_final_levels, update.hydro_final_levels)
    _update_1_level_mapping(base.hydro_generation_power, update.hydro_generation_power)
    _update_1_level_mapping(base.solar, update.solar)
    _update_1_level_mapping(base.wind, update.wind)
    _update_1_level_mapping(base.binding_constraints, update.binding_constraints)
    _update_2_levels_mapping(base.renewable, update.renewable)
    _update_2_levels_mapping(base.storage_inflows, update.storage_inflows)
    _update_1_level_mapping(base.ntc, update.ntc)
    _update_3_levels_mapping(base.storage_constraints, update.storage_constraints)
    # Validate the final ruleset
    validate_ruleset_against_version(version, base)
