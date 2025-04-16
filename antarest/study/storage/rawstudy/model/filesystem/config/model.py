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

from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Set

from antares.study.version import StudyVersion
from pydantic import Field, model_validator
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.utils import DTO
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.model import StudyVersionInt

from .binding_constraint import (
    DEFAULT_GROUP,
    DEFAULT_OPERATOR,
    DEFAULT_TIMESTEP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from .renewable import RenewableConfigType
from .st_storage import STStorageConfigType
from .validation import extract_filtering, study_version_context


class EnrModelling(EnumIgnoreCase):
    """
    Renewable energy modelling type (since v8.1).

    Attributes:
        AGGREGATED: Simulations are done using aggregated data from wind and solar.
        CLUSTERS: Simulations are done using renewable clusters
    """

    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"

    @override
    def __str__(self) -> str:
        """Return the string representation of the enum value."""
        return self.value


class Link(AntaresBaseModel, extra="ignore"):
    """
    Object linked to /input/links/<link>/properties.ini information

    Attributes:
        filters_synthesis: list of filters for synthesis data
        filters_year: list of filters for year-by-year data

    Notes:
        Ignore extra fields, because we only need `filter-synthesis` and `filter-year-by-year`.
    """

    filters_synthesis: List[str] = Field(default_factory=list)
    filters_year: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    def validation(cls, values: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        # note: field names are in kebab-case in the INI file
        filters_synthesis = values.pop("filter-synthesis", values.pop("filters_synthesis", ""))
        filters_year = values.pop("filter-year-by-year", values.pop("filters_year", ""))
        values["filters_synthesis"] = extract_filtering(filters_synthesis)
        values["filters_year"] = extract_filtering(filters_year)
        return values


class Area(AntaresBaseModel, extra="forbid"):
    """
    Object linked to /input/<area>/optimization.ini information
    """

    name: str
    links: Dict[str, Link]
    thermals: List[ThermalCluster]
    renewables: List[RenewableConfigType]
    filters_synthesis: List[str]
    filters_year: List[str]
    # since v8.6
    st_storages: List[STStorageConfigType] = []


class DistrictSet(AntaresBaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL: List[str] = ["hourly", "daily", "weekly", "monthly", "annual"]
    name: Optional[str] = None
    inverted_set: bool = False
    areas: Optional[List[str]] = None
    output: bool = True
    filters_synthesis: List[str] = ALL
    filters_year: List[str] = ALL

    def get_areas(self, all_areas: List[str]) -> List[str]:
        areas = self.areas or []
        if self.inverted_set:
            areas = list(set(all_areas).difference(set(areas)))
        return sorted(areas)


class Simulation(AntaresBaseModel):
    """
    Object linked to /output/<simulation_name>/about-the-study/** information
    """

    name: str
    date: str
    mode: str
    nbyears: int
    synthesis: bool
    by_year: bool
    error: bool
    playlist: Optional[List[int]]
    archived: bool = False
    xpansion: str

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq", "draft": "dft"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"


class BindingConstraintDTO(AntaresBaseModel):
    """
    Object linked to `input/bindingconstraints/bindingconstraints.ini` information

    Attributes:
        id: The ID of the binding constraint.
        areas: List of area IDs on which the BC applies (links or clusters).
        clusters: List of thermal cluster IDs on which the BC applies (format: "area.cluster").
        time_step: The time_step of the BC
        operator: The operator of the BC
        group: The group for the scenario of BC (optional, required since v8.7).
    """

    id: str
    areas: Set[str]
    clusters: Set[str]
    time_step: BindingConstraintFrequency = DEFAULT_TIMESTEP
    operator: BindingConstraintOperator = DEFAULT_OPERATOR
    # since v8.7
    group: str = DEFAULT_GROUP


class FileStudyTreeConfig(DTO):
    """
    Root object to handle all study parameters which impact tree structure
    """

    def __init__(
        self,
        study_path: Path,
        path: Path,
        study_id: str,
        version: StudyVersion,
        output_path: Optional[Path] = None,
        areas: Optional[Dict[str, Area]] = None,
        sets: Optional[Dict[str, DistrictSet]] = None,
        outputs: Optional[Dict[str, Simulation]] = None,
        bindings: Optional[List[BindingConstraintDTO]] = None,
        store_new_set: bool = False,
        archive_input_series: Optional[List[str]] = None,
        enr_modelling: str = str(EnrModelling.AGGREGATED),
        archive_path: Optional[Path] = None,
    ):
        self.study_path = study_path
        self.path = path
        self.study_id = study_id
        self.version = version
        self.output_path = output_path
        self.areas = areas or {}
        self.sets = sets or {}
        self.outputs = outputs or {}
        self.bindings = bindings or []
        self.store_new_set = store_new_set
        self.archive_input_series = archive_input_series or []
        self.enr_modelling = enr_modelling
        self.archive_path = archive_path

    def next_file(self, name: str, is_output: bool = False) -> "FileStudyTreeConfig":
        if is_output and name in self.outputs and self.outputs[name].archived:
            archive_path: Optional[Path] = self.path / f"{name}.zip"
        else:
            archive_path = self.archive_path

        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=self.path / name,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            archive_path=archive_path,
        )

    def at_file(self, filepath: Path) -> "FileStudyTreeConfig":
        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=filepath,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
        )

    def area_names(self) -> List[str]:
        return list(self.areas)

    def set_names(self, only_output: bool = True) -> List[str]:
        return [k for k, v in self.sets.items() if v.output or not only_output]

    def get_thermal_ids(self, area: str) -> List[str]:
        """
        Returns a list of thermal cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return [th.id for th in self.areas[area].thermals]

    def get_renewable_ids(self, area: str) -> List[str]:
        """
        Returns a list of renewable cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return [r.id for r in self.areas[area].renewables]

    def get_st_storage_ids(self, area: str) -> List[str]:
        return [s.id for s in self.areas[area].st_storages]

    def get_links(self, area: str) -> List[str]:
        return list(self.areas[area].links)

    def get_binding_constraint_groups(self) -> List[str]:
        """
        Returns the list of binding constraint groups, without duplicates and
        sorted alphabetically (case-insensitive).
        Note that groups are stored in lower case in the binding constraints file.
        """
        lower_groups = {bc.group.lower(): bc.group for bc in self.bindings}
        return [grp for _, grp in sorted(lower_groups.items())]

    def get_filters_synthesis(self, area: str, link: Optional[str] = None) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_synthesis
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_synthesis
        return self.areas[area].filters_synthesis

    def get_filters_year(self, area: str, link: Optional[str] = None) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_year
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_year
        return self.areas[area].filters_year


class FileStudyTreeConfigDTO(AntaresBaseModel):
    study_path: Path
    path: Path
    study_id: str
    version: StudyVersionInt
    output_path: Optional[Path] = None
    areas: Dict[str, Area] = dict()
    sets: Dict[str, DistrictSet] = dict()
    outputs: Dict[str, Simulation] = dict()
    bindings: List[BindingConstraintDTO] = list()
    store_new_set: bool = False
    archive_input_series: List[str] = list()
    enr_modelling: str = str(EnrModelling.AGGREGATED)
    archive_path: Optional[Path] = None

    @staticmethod
    def from_build_config(
        config: FileStudyTreeConfig,
    ) -> "FileStudyTreeConfigDTO":
        return FileStudyTreeConfigDTO.model_construct(
            study_path=config.study_path,
            path=config.path,
            study_id=config.study_id,
            version=config.version,
            output_path=config.output_path,
            areas=config.areas,
            sets=config.sets,
            outputs=config.outputs,
            bindings=config.bindings,
            store_new_set=config.store_new_set,
            archive_input_series=config.archive_input_series,
            enr_modelling=config.enr_modelling,
            archive_path=config.archive_path,
        )

    def to_build_config(self) -> FileStudyTreeConfig:
        return FileStudyTreeConfig(
            study_path=self.study_path,
            path=self.path,
            study_id=self.study_id,
            version=self.version,
            output_path=self.output_path,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            archive_path=self.archive_path,
        )


def validate_config(version: StudyVersion, data: Dict[str, Any]) -> FileStudyTreeConfig:
    """
    Parses the provided data, assuming the provided study version.

    The instantiation of some of the config objects depend on the study version
    (thermal clusters, etc).
    """
    return FileStudyTreeConfigDTO.model_validate(data, context=study_version_context(version)).to_build_config()
