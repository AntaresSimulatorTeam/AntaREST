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
from typing import Iterable, Literal, Mapping, TypeAlias

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


RandType: TypeAlias = Literal[""]
Value: TypeAlias = float | int | RandType
AreaId: TypeAlias = str
LinkId: TypeAlias = str
ObjectId: TypeAlias = str
ConstraintId: TypeAlias = str
McYearToTimeSeries: TypeAlias = dict[str, Value]
McYearToValue: TypeAlias = dict[str, Value]
AreaScenarios: TypeAlias = dict[AreaId, McYearToTimeSeries]

LinkScenarios: TypeAlias = dict[LinkId, McYearToTimeSeries]
AreaItemsScenarios: TypeAlias = dict[AreaId, dict[ObjectId, McYearToTimeSeries]]
AdditionalConstraintScenarios: TypeAlias = dict[AreaId, dict[ObjectId, dict[ConstraintId, McYearToTimeSeries]]]
HydroLevelsScenarios: TypeAlias = dict[AreaId, McYearToValue]

RANDOM: RandType = ""


class Ruleset(AntaresBaseModel, populate_by_name=True, extra="forbid"):
    """
    A ruleset defines, for each item in the study, a mapping of MC year to the data to be used.

    In the vast majority of cases, the data is simply a timeseries number to be used,
    but for specific cases it can be an actual value, like the level of an hydro reservoir.
    """

    load: AreaScenarios | None = Field(default=None, alias="l")
    thermal: AreaItemsScenarios | None = Field(default=None, alias="t")
    hydro: AreaScenarios | None = Field(default=None, alias="h")
    hydro_initial_levels: HydroLevelsScenarios | None = Field(default=None, alias="hl")
    hydro_final_levels: HydroLevelsScenarios | None = Field(default=None, alias="hfl")
    hydro_generation_power: AreaScenarios | None = Field(default=None, alias="hgp")
    wind: AreaScenarios | None = Field(default=None, alias="w")
    solar: AreaScenarios | None = Field(default=None, alias="s")
    ntc: AreaScenarios | None = Field(default=None, alias="ntc")
    renewable: AreaItemsScenarios | None = Field(default=None, alias="r")
    binding_constraints: AreaScenarios | None = Field(default=None, alias="bc")
    storage_inflows: AreaItemsScenarios | None = Field(default=None, alias="sts")


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
        return self._thermals

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


def initialize_ruleset(years: list[str], index: StudyIndex) -> Ruleset:
    """
    Creates a ruleset initialized with random ("") for all items and years of a study.
    """
    return Ruleset(
        load=_create_scenarios_mapping(names=index.area_ids, years=years),
        thermal=_create_cluster_scenarios_mapping(names=index.thermal_ids, years=years),
        hydro=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_initial_levels=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_final_levels=_create_scenarios_mapping(names=index.area_ids, years=years),
        hydro_generation_power=_create_scenarios_mapping(names=index.area_ids, years=years),
        solar=_create_scenarios_mapping(names=index.area_ids, years=years),
        wind=_create_scenarios_mapping(names=index.area_ids, years=years),
        renewable=_create_cluster_scenarios_mapping(names=index.renewable_ids, years=years),
        storage_inflows=_create_cluster_scenarios_mapping(names=index.storage_ids, years=years),
        binding_constraints=_create_scenarios_mapping(names=index.bc_group_ids, years=years),
        ntc=_create_scenarios_mapping(names=index.link_ids, years=years),
    )
