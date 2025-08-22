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
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree


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

    @override
    def __str__(self) -> str:
        """Return the string representation of the enum value."""
        return self.value


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

    def get(self, scenario_type: ScenarioType) -> AreaScenarios | AreaItemsScenarios:
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

    def set(self, scenario_type: ScenarioType, scenarios: AreaScenarios | AreaItemsScenarios) -> None:
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


Rulesets: TypeAlias = dict[str, Ruleset]


class StudyIndex:
    """
    A class containing information about all identifiable objects IDs and names of a study.
    """

    def __init__(
        self,
        areas: Iterable[str],
        links: Iterable[tuple[str, str]],
        thermals: Mapping[str, Iterable[str]],
        storages: Mapping[str, Iterable[str]],
        bc_groups: Iterable[str],
        renewables: Mapping[str, Iterable[str]],
    ):
        # TODO: to_id
        self._areas = {a.lower(): a for a in areas}
        self._links = {(a1.lower(), a2.lower()): (a1, a2) for a1, a2 in links}
        self._thermals = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in thermals.items()}
        self._renewables = {a.lower(): {cl.lower(): cl for cl in clusters} for a, clusters in renewables.items()}
        self._storages = {
            a.lower(): {a_storage.lower(): a_storage for a_storage in a_storages} for a, a_storages in storages.items()
        }
        self._bc_groups = {g.lower(): g for g in bc_groups}

    @property
    def area_ids(self) -> Iterable[str]:
        return self._areas.keys()

    def area_name(self, area_id: str) -> str:
        return self._areas[area_id]

    @property
    def thermal_ids(self) -> Mapping[str, Iterable[str]]:
        return self._thermals

    def area_thermal_ids(self, area: str) -> Iterable[str]:
        return self._thermals[transform_name_to_id(area)]

    @property
    def renewable_ids(self) -> Mapping[str, Iterable[str]]:
        return self._renewables

    @property
    def bc_group_ids(self) -> Iterable[str]:
        return self._bc_groups

    @property
    def storage_ids(self) -> Mapping[str, Iterable[str]]:
        return self._storages

    @property
    def link_ids(self) -> Iterable[str]:
        return [f"{a1} / {a2}" for a1, a2 in self._links.keys()]


def study_index(file_study: FileStudyTree) -> StudyIndex:
    areas = file_study.config.areas
    return StudyIndex(
        areas=file_study.config.areas,
        links=((a1, a2) for a1 in areas for a2 in file_study.config.get_links(a1)),
        bc_groups=file_study.config.get_binding_constraint_groups(),
        thermals={a: file_study.config.get_thermal_ids(a) for a in areas},
        renewables={a: file_study.config.get_renewable_ids(a) for a in areas},
        storages={a: file_study.config.get_st_storage_ids(a) for a in areas},
    )


def _create_scenarios_mapping(names: Iterable[str], years: list[str]) -> AreaScenarios:
    return {n: {y: RANDOM for y in years} for n in names}


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


def _update_mapping(base: McYearToTimeSeries, update: McYearToTimeSeries) -> None:
    base.update(update)


def _update_simple_mapping(base: _OneLevelScenarios, update: _OneLevelScenarios) -> None:
    for name, mapping in update.items():
        _update_mapping(base.setdefault(name, {}), mapping)


def _update_double_mapping(base: _TwoLevelScenarios, update: _TwoLevelScenarios) -> None:
    for name, mapping in update.items():
        _update_simple_mapping(base.setdefault(name, {}), mapping)


def update_ruleset(base: Ruleset, update: Ruleset) -> None:
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
