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

from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from antares.study.version import StudyVersion
from pydantic import Field, model_validator
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.utils import DTO
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.config.general_model import Mode
from antarest.study.business.model.district_model import District
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.study_index import StudyIndex
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.model import STUDY_VERSION_9_2, StudyVersionInt

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


class LinkConfig(AntaresBaseModel, extra="ignore"):
    """
    Object linked to /input/links/<link>/properties.ini information
    Attributes:
        filters_synthesis: list of filters for synthesis data
        filters_year: list of filters for year-by-year data
    Notes:
        Ignore extra fields, because we only need `filter-synthesis` and `filter-year-by-year`.
    """

    filters_synthesis: list[str] = Field(default_factory=list)
    filters_year: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    def validation(cls, values: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        # note: field names are in kebab-case in the INI file
        filters_synthesis = values.pop("filter-synthesis", values.pop("filters_synthesis", ""))
        filters_year = values.pop("filter-year-by-year", values.pop("filters_year", ""))
        values["filters_synthesis"] = extract_filtering(filters_synthesis)
        values["filters_year"] = extract_filtering(filters_year)
        return values


class AreaConfig(AntaresBaseModel, extra="forbid"):
    """
    Object linked to /input/<area> configuration information
    """

    name: str
    links: dict[str, LinkConfig]
    thermals: list[ThermalCluster]
    renewables: list[RenewableCluster]
    filters_synthesis: list[str]
    filters_year: list[str]
    # since v8.6
    st_storages: list[STStorage] = []
    # Since v9.2, dictionary storage ID -> constraints
    st_storages_additional_constraints: dict[str, list[STStorageAdditionalConstraint]] = {}


class Simulation(AntaresBaseModel):
    """
    Object linked to /output/<simulation_name>/about-the-study/** information
    """

    name: str
    date: str
    mode: Mode
    nbyears: int
    synthesis: bool
    by_year: bool
    error: bool
    playlist: list[int] | None
    archived: bool = False
    xpansion: str

    def get_file(self) -> str:
        dash = "-" if self.name else ""
        return f"{self.date}{self.mode.get_output_suffix()}{dash}{self.name}"


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
        output_path: Path | None = None,
        districts: dict[str, District] | None = None,
        areas: dict[str, AreaConfig] | None = None,
        outputs: dict[str, Simulation] | None = None,
        bindings_groups: set[str] | None = None,
        store_new_set: bool = False,
        archive_input_series: list[str] | None = None,
        enr_modelling: str = str(EnrModelling.AGGREGATED),
        archive_path: Path | None = None,
    ):
        self.study_path = study_path
        self.path = path
        self.study_id = study_id
        self.version = version
        self.output_path = output_path
        self.areas = areas or {}
        self.districts = districts or {}
        self.outputs = outputs or {}
        self.bindings_groups = bindings_groups or set()
        self.store_new_set = store_new_set
        self.archive_input_series = archive_input_series or []
        self.enr_modelling = enr_modelling
        self.archive_path = archive_path

    def next_file(self, name: str, is_output: bool = False) -> "FileStudyTreeConfig":
        if is_output and name in self.outputs and self.outputs[name].archived:
            archive_path: Path | None = self.path / f"{name}.zip"
        else:
            archive_path = self.archive_path

        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=self.path / name,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            districts=self.districts,
            outputs=self.outputs,
            bindings_groups=self.bindings_groups,
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
            districts=self.districts,
            outputs=self.outputs,
            bindings_groups=self.bindings_groups,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
        )

    def area_names(self) -> list[str]:
        return list(self.areas)

    def get_thermal_ids(self, area: str) -> list[str]:
        """
        Returns a list of thermal cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return [th.id for th in self.areas[area].thermals]

    def get_renewable_ids(self, area: str) -> list[str]:
        """
        Returns a list of renewable cluster IDs for a given area.
        Note that IDs may not be in lower case (but series IDs are).
        """
        return [r.id for r in self.areas[area].renewables]

    def get_st_storage_ids(self, area: str) -> list[str]:
        return [s.id for s in self.areas[area].st_storages]

    def get_links(self, area: str) -> list[str]:
        return list(self.areas[area].links)

    def get_binding_constraint_groups(self) -> list[str]:
        """
        Returns the list of binding constraint groups, without duplicates and
        sorted alphabetically (case-insensitive).
        Note that groups are stored in lower case in the binding constraints file.
        """

        return sorted(self.bindings_groups)

    def get_sts_constraint_ids(self, area: str, storage: str) -> list[str]:
        if self.version >= STUDY_VERSION_9_2:
            return [c.id for c in self.areas[area].st_storages_additional_constraints[storage]]
        else:
            return []

    def to_study_index(self) -> StudyIndex:
        areas = self.areas
        sts_additional_constraints = {}
        if self.version >= STUDY_VERSION_9_2:
            sts_additional_constraints = {
                a: {s: self.get_sts_constraint_ids(a, s) for s in self.get_st_storage_ids(a)} for a in areas
            }
        return StudyIndex(
            areas=areas,
            links=((a1, a2) for a1 in areas for a2 in self.get_links(a1)),
            bc_groups=self.get_binding_constraint_groups(),
            thermals={a: self.get_thermal_ids(a) for a in areas},
            renewables={a: self.get_renewable_ids(a) for a in areas},
            storages={a: self.get_st_storage_ids(a) for a in areas},
            sts_additional_constraints=sts_additional_constraints,
        )


class FileStudyTreeConfigDTO(AntaresBaseModel):
    study_path: Path
    path: Path
    study_id: str
    version: StudyVersionInt
    output_path: Path | None = None
    districts: dict[str, District] = dict()
    areas: dict[str, AreaConfig] = dict()
    outputs: dict[str, Simulation] = dict()
    bindings_groups: set[str] | None = None
    store_new_set: bool = False
    archive_input_series: list[str] = list()
    enr_modelling: str = str(EnrModelling.AGGREGATED)
    archive_path: Path | None = None

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
            districts=config.districts,
            outputs=config.outputs,
            bindings_groups=config.bindings_groups,
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
            districts=self.districts,
            outputs=self.outputs,
            bindings_groups=self.bindings_groups,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            archive_path=self.archive_path,
        )


def validate_config(version: StudyVersion, data: dict[str, Any]) -> FileStudyTreeConfig:
    """
    Parses the provided data, assuming the provided study version.

    The instantiation of some of the config objects depend on the study version
    (thermal clusters, etc).
    """
    return FileStudyTreeConfigDTO.model_validate(data, context=study_version_context(version)).to_build_config()
