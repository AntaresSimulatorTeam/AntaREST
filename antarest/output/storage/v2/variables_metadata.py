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
Design:
variables metadata are stored in tables so that we can retrieve for each variable:
 - its name
 - its unit
 - the statistic name

and so that we know for each object of the study what were the output variables for that object.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from functools import cached_property
from itertools import groupby
from pathlib import Path
from typing import Callable, Iterable, NewType, Type, TypeAlias, TypeVar, Literal, overload

from mypyc.ir.ops import Generic
from pydantic import BaseModel
from sqlalchemy import Column, String, Table, select
from sqlalchemy.orm import Session

from antarest.core.utils.collection_utils import find_first, find_if
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.output.filestudy.iteration import identify_mc_ind_files
from antarest.output.filestudy.utils import (
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    QueryFileType,
    get_start_column,
    parse_headers,
)
from antarest.output.model import (
    AreaMcAllVariables,
    AreaMcIndVariables,
    ComponentMcAllVariables,
    ComponentMcIndVariables,
    LinkMcAllVariables,
    LinkMcIndVariables,
    McAllVar,
    McIndVar,
    OutputVariablesList,
    SystemMcAllVariables,
    SystemMcIndVariables,
    VariableDescription,
)
from antarest.output.utils import find_mode_dir
from antarest.study.model import MatrixFrequency

metadata = Base.metadata


OUTPUT_VARIABLES_TABLE = Table(
    "output_v2_variable_defs",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("variables", String),
)


class _BaseModel(BaseModel, extra="forbid", populate_by_name=True, frozen=True):
    pass


class ParquetMcIndVariableDescription(_BaseModel):
    name: str
    unit: str
    column_index: int


class ParquetMcAllVariableDescription(_BaseModel):
    name: str
    unit: str
    statistic_type: str
    column_index: int


class ParquetThermalClusterVariables(_BaseModel):
    area_id: str
    cluster_id: str
    variables: list[int]  # index in the global variables list


class ParquetRenewableClusterVariables(_BaseModel):
    area_id: str
    cluster_id: str
    variables: list[int]  # index in the global variables list


class ParquetShortTermStorageVariables(_BaseModel):
    area_id: str
    storage_id: str
    variables: list[int]  # index in the global variables list


class ParquetLinkVariables(_BaseModel):
    area1_id: str
    area2_id: str
    variables: list[int]


class ParquetAreaVariables(_BaseModel):
    area_id: str
    variables: list[int]


class ParquetVariablesMetadata(_BaseModel):
    """
    Metadata about all variables present in the output
    """

    # All variables, for all objects
    mc_ind_variables: list[ParquetMcIndVariableDescription]
    mc_all_variables: list[ParquetMcAllVariableDescription]

    # Follow the lists of variables for each object in the system..
    area_variables: list[ParquetAreaVariables]
    link_variables: list[ParquetLinkVariables]
    thermal_cluster_variables: list[ParquetThermalClusterVariables]
    renewable_cluster_variables: list[ParquetRenewableClusterVariables]
    short_term_storage_variables: list[ParquetShortTermStorageVariables]


def _convert_parquet_variables_metadata(parquet_variables: ParquetVariablesMetadata) -> OutputVariablesList:
    """
    Convert the compact parquet representation to the public variable model.
    (AI generated boilerplate)
    """

    ind_variables = [McIndVar(name=var.name, unit=var.unit) for var in parquet_variables.mc_ind_variables]
    all_variables = [
        McAllVar(name=var.name, unit=var.unit, stat=var.statistic_type) for var in parquet_variables.mc_all_variables
    ]

    def components(
        assignments: list[ParquetThermalClusterVariables]
        | list[ParquetRenewableClusterVariables]
        | list[ParquetShortTermStorageVariables],
    ) -> tuple[list[ComponentMcIndVariables], list[ComponentMcAllVariables]]:
        ind: list[ComponentMcIndVariables] = []
        all_: list[ComponentMcAllVariables] = []
        for assignment in assignments:
            component_name = getattr(assignment, "cluster_id", None) or assignment.storage_id
            ind.append(
                ComponentMcIndVariables(
                    component_name=component_name, variables=[ind_variables[i] for i in assignment.variables]
                )
            )
            all_.append(
                ComponentMcAllVariables(
                    component_name=component_name, variables=[all_variables[i] for i in assignment.variables]
                )
            )
        return ind, all_

    ind_areas: list[AreaMcIndVariables] = []
    all_areas: list[AreaMcAllVariables] = []
    for area in parquet_variables.area_variables:
        thermal_ind, thermal_all = components(
            [item for item in parquet_variables.thermal_cluster_variables if item.area_id == area.area_id]
        )
        renewable_ind, renewable_all = components(
            [item for item in parquet_variables.renewable_cluster_variables if item.area_id == area.area_id]
        )
        storage_ind, storage_all = components(
            [item for item in parquet_variables.short_term_storage_variables if item.area_id == area.area_id]
        )
        ind_areas.append(
            AreaMcIndVariables(
                area_name=area.area_id,
                variables=[ind_variables[i] for i in area.variables],
                thermal_clusters=thermal_ind,
                renewable_clusters=renewable_ind,
                short_term_storages=storage_ind,
            )
        )
        all_areas.append(
            AreaMcAllVariables(
                area_name=area.area_id,
                variables=[all_variables[i] for i in area.variables],
                thermal_clusters=thermal_all,
                renewable_clusters=renewable_all,
                short_term_storages=storage_all,
            )
        )

    ind_links = [
        LinkMcIndVariables(
            area_1_name=link.area1_id, area_2_name=link.area2_id, variables=[ind_variables[i] for i in link.variables]
        )
        for link in parquet_variables.link_variables
    ]
    all_links = [
        LinkMcAllVariables(
            area_1_name=link.area1_id, area_2_name=link.area2_id, variables=[all_variables[i] for i in link.variables]
        )
        for link in parquet_variables.link_variables
    ]
    return OutputVariablesList(
        mc_ind=SystemMcIndVariables(areas=ind_areas, links=ind_links),
        mc_all=SystemMcAllVariables(areas=all_areas, links=all_links),
    )


def find_first_year_dir(mc_ind_dir: Path) -> Path:
    for year_dir in mc_ind_dir.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            return year_dir
    raise ValueError("No valid year directory found in mc-ind")


@dataclass(frozen=True)
class OutputFileMapping:
    path: Path
    mc_year: int | None
    element_id: str
    file_type: QueryFileType
    frequency: MatrixFrequency


def find_mc_years(output_dir: Path) -> list[int]:
    mode_dir = find_mode_dir(output_dir)
    mc_ind_dir = mode_dir / "mc-ind"
    if not mc_ind_dir.exists():
        return []
    return sorted(int(d.name) for d in mc_ind_dir.iterdir())


@dataclass(frozen=True)
class FileVariable:
    """
    Describes variable metadata as described in data files, together with their position in the table,
    to allow for easier retrieval.
    """

    variable: VariableDescription
    source_col: int


@dataclass(frozen=True)
class VariableMapping:
    """
    Mapping of a variable from source data files to the target parquet file.
    """

    variable: VariableDescription
    source_col: int
    target_col: int


class McIndFileOutput:
    """
    Provides a collection of methods to inspect the content of a mc-ind output directory.

    Attributes:
        output_dir (Path): The path to the output directory typically (<study_dir>/outputs/<output_id>).
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    @cached_property
    def mc_years(self) -> list[int]:
        return find_mc_years(self.output_dir)

    @property
    def first_mc_year(self) -> int:
        return self.mc_years[0]

    @cached_property
    def mode(self) -> str:
        return find_mode_dir(self.output_dir).name

    def get_mc_year_dir(self, year: int) -> Path:
        return self.output_dir / self.mode / "mc-ind" / f"{year:05d}"

    @cached_property
    def link_ids(self) -> list[str]:
        """
        IDs of links that have data in the output directory, sorted.
        """
        return sorted(d.name for d in self.iter_links_dir(self.first_mc_year))

    @cached_property
    def area_ids(self) -> list[str]:
        """
        IDs of areas that have data in the output directory, sorted.
        """
        return sorted(d.name for d in self.iter_areas_dir(self.first_mc_year))

    def iter_areas_dir(self, mc_year: int) -> Iterable[Path]:
        """
        No ordering guarantee.
        """
        return (self.get_mc_year_dir(mc_year) / "areas").iterdir()

    def iter_links_dir(self, mc_year: int) -> Iterable[Path]:
        """
        No ordering guarantee.
        """
        return (self.get_mc_year_dir(mc_year) / "links").iterdir()

    def get_file(
        self,
        mc_year: int,
        file_type: MCIndAreasQueryFile | MCIndLinksQueryFile,
        area_id: str,
        frequency: MatrixFrequency,
    ) -> Path | None:
        """
        Returns the path corresponding to the specified data, if it exists.
        """
        element_type = "areas" if isinstance(file_type, MCIndAreasQueryFile) else "links"
        file_path = self.get_mc_year_dir(mc_year) / element_type / area_id / f"{file_type}-{frequency}.txt"
        return file_path if file_path.exists() else None


def build_mc_ind_output_mapping(output_dir: Path) -> list[OutputFileMapping]:
    """
    Retrieves all data file paths together with some metadata.
    This then allows to inspect data more easily, while being quite fast to execute on a reasonably fast disk.
    """
    res = []

    mode_dir = find_mode_dir(output_dir)
    mc_ind_dir = mode_dir / "mc-ind"
    if mc_ind_dir.exists():
        for year_dir in mc_ind_dir.iterdir():
            year = int(year_dir.name)
            for area_dir in (year_dir / "areas").iterdir():
                area_id = area_dir.name
                for file_type, freq in itertools.product(MCIndAreasQueryFile, MatrixFrequency):
                    file_name = f"{file_type}-{freq}.txt"
                    file_path = area_dir / file_name
                    if (area_dir / file_name).exists():
                        res.append(
                            OutputFileMapping(
                                file_type=file_type, frequency=freq, element_id=area_id, mc_year=year, path=file_path
                            )
                        )

            for link_dir in (year_dir / "links").iterdir():
                link_id = link_dir.name
                for file_type, freq in itertools.product(MCIndLinksQueryFile, MatrixFrequency):
                    file_name = f"{file_type}-{freq}.txt"
                    file_path = link_dir / file_name
                    if (link_dir / file_name).exists():
                        res.append(
                            OutputFileMapping(
                                file_type=file_type, frequency=freq, element_id=link_id, mc_year=year, path=file_path
                            )
                        )
    return res


def build_mc_ind_output_mapping_2(output_dir: Path) -> list[OutputFileMapping]:
    """
    Retrieves all data file paths together with some metadata.
    This then allows to inspect data more easily, while being quite fast to execute on a reasonably fast disk.
    """
    res = []

    output = McIndFileOutput(output_dir)
    for year in output.mc_years:
        for area_id in output.area_ids:
            for file_type, freq in itertools.product(MCIndAreasQueryFile, MatrixFrequency):
                if file_path := output.get_file(year, file_type, area_id, freq):
                    res.append(
                        OutputFileMapping(
                            file_type=file_type, frequency=freq, element_id=area_id, mc_year=year, path=file_path
                        )
                    )

        for link_id in output.link_ids:
            for file_type, freq in itertools.product(MCIndLinksQueryFile, MatrixFrequency):
                if file_path := output.get_file(year, file_type, link_id, freq):
                    res.append(
                        OutputFileMapping(
                            file_type=file_type, frequency=freq, element_id=link_id, mc_year=year, path=file_path
                        )
                    )
    return res


def find_representative_files(
    output: McIndFileOutput, file_type: MCIndAreasQueryFile | MCIndLinksQueryFile
) -> list[OutputFileMapping]:
    # We may have different "frequencies" depending on the areas and links
    # but for a given area or link, we'll have the same variables for all "frequencies"
    # Therefore, we only need to identify variables for one of those frequencies

    output_files = []
    first_year = output.first_mc_year
    match file_type:
        case MCIndAreasQueryFile():
            element_ids = output.area_ids
        case MCIndLinksQueryFile():
            element_ids = output.link_ids

    for element_id in element_ids:
        for freq in MatrixFrequency:
            if data_file := output.get_file(first_year, file_type, element_id, freq):
                output_files.append(OutputFileMapping(data_file, first_year, element_id, file_type, freq))
                continue  # other frequencies will have the same variables
    return output_files


@dataclass(frozen=True)
class FileMappings:
    """
    Mapping of variables to column for each type of file, for each item in the system
    """

    area_values_mappings: dict[str, list[FileVariable]]
    area_details_mappings: dict[str, list[FileVariable]]
    area_details_res_mappings: dict[str, list[FileVariable]]
    area_details_sts_mappings: dict[str, list[FileVariable]]
    link_values_mappings: dict[str, list[FileVariable]]


def get_mappings(output: McIndFileOutput) -> FileMappings:
    return FileMappings(
        area_values_mappings=get_file_type_mappings(output, MCIndAreasQueryFile.VALUES),
        area_details_mappings=get_file_type_mappings(output, MCIndAreasQueryFile.DETAILS),
        area_details_res_mappings=get_file_type_mappings(output, MCIndAreasQueryFile.DETAILS_RES),
        area_details_sts_mappings=get_file_type_mappings(output, MCIndAreasQueryFile.DETAILS_ST_STORAGE),
        link_values_mappings=get_file_type_mappings(output, MCIndLinksQueryFile.VALUES),
    )


def get_file_type_mappings(
    output: McIndFileOutput, file_type: MCIndAreasQueryFile | MCIndLinksQueryFile
) -> dict[str, list[FileVariable]]:
    res: dict[str, list[FileVariable]] = {}

    for f in find_representative_files(output, file_type):
        with open(f.path, "r", encoding="utf-8") as file:
            vars_desc = parse_headers(file, get_start_column(f.frequency))
            res[f.element_id] = [FileVariable(variable=v, source_col=i) for i, v in enumerate(vars_desc)]
    return res


# Keys for uniquely identifying files.
# In particular, thermal clusters etc don't map to a whole file, their data is a sub-part of an area file

AreaFileKey = NewType("AreaFileKey", str)

@dataclass(frozen=True, slots=True)
class LinkFileKey:
    area1_id: str
    area2_id: str

FileKey: TypeAlias = AreaFileKey | LinkFileKey
FK = TypeVar("FK", AreaFileKey, LinkFileKey)

# Follow definitions of proper system items, which don't necessarily map to a whole file
# In our target parquet format, each item will have a corresponding row in the corresponding parquet file

AreaId = NewType("AreaId", str)


@dataclass(frozen=True, slots=True)
class LinkId:
    area1_id: str
    area2_id: str

@dataclass(frozen=True, slots=True)
class ThermalClusterId:
    area_id: str
    cluster_id: str

@dataclass(frozen=True, slots=True)
class RenewableClusterId:
    area_id: str
    cluster_id: str


@dataclass(frozen=True, slots=True)
class ShortTermStorageId:
    area_id: str
    storage_id: str

ItemId: TypeAlias = AreaId | LinkId | ThermalClusterId | RenewableClusterId | ShortTermStorageId

ID = TypeVar("ID", AreaId, LinkId, ThermalClusterId, RenewableClusterId, ShortTermStorageId)

@dataclass(frozen=True, slots=True)
class SystemVariables:
    area_variables: ItemsVariables[AreaId]
    link_variables: ItemsVariables[LinkId]
    thermal_cluster_variables: ItemsVariables[ThermalClusterId]
    renewable_cluster_variables: ItemsVariables[RenewableClusterId]
    short_term_storage_variables: ItemsVariables[ShortTermStorageId]

@dataclass(frozen=True, slots=True)
class VariableRefs(Generic[ID]):
    """
    list of variable indices for a given item (area or link or cluster or ...)
    """
    item_id: ID
    variables_refs: list[int]


@dataclass(frozen=True, slots=True)
class ItemsVariables(Generic[ID]):
    """
    The list of variables for a given item type, together with references for each item.

    The indices in "refs" are the indices of the variables in "variables".
    """
    variables: list[VariableDescription]
    refs: list[VariableRefs[ID]]


@overload
def file_mapping_to_items_variables(
    item_type: Literal["area"],
    mapping: dict[FK, list[FileVariable]],
    var_indices: dict[VariableDescription, int],
) -> ItemsVariables[ID]:
    pass

def file_mapping_to_items_variables(
    item_type: Literal["area", "link", "thermal_cluster", "renewable_cluster", "short_term_storage"],
    mapping: dict[FK, list[FileVariable]],
    var_indices: dict[VariableDescription, int],
) -> ItemsVariables[ID]:
    """
        Transforms the input mapping into a list of "parquet variables", populating the list of variables and
        their indices along the way.
        """
    variables: list[VariableDescription] = []
    variables_indices: dict[VariableDescription, int] = {}
    variables_refs: dict[ID, list[int]] = {}

    for item_id, vars in mapping.items():
        local_var_indices: list[int] = []
        for v in vars:
            var_desc = v.variable
            if var_desc in var_indices:
                local_var_indices.append(var_indices[var_desc])
            else:
                var_count = len(var_indices)
                local_var_indices.append(len(var_indices))
                var_indices[var_desc] = var_count
        parquet_vars = cls(area, local_var_indices)
        res.append(parquet_vars)
    return res



T = TypeVar("T", ParquetAreaVariables, ParquetLinkVariables)


def file_mapping_to_parquet_vars(
    mapping: dict[str, list[FileVariable]],
    var_indices: dict[VariableDescription, int],
    cls: Type[T],
) -> list[T]:
    """
        Transforms the input mapping into a list of "parquet variables", populating the list of variables and
        their indices along the way.
        """
    res: list[T] = []
    for area, vars in mapping.items():
        local_var_indices: list[int] = []
        for v in vars:
            var_desc = v.variable
            if var_desc in var_indices:
                local_var_indices.append(var_indices[var_desc])
            else:
                var_count = len(var_indices)
                local_var_indices.append(len(var_indices))
                var_indices[var_desc] = var_count
        parquet_vars = cls(area, local_var_indices)
        res.append(parquet_vars)
    return res

U = TypeVar("U", ParquetThermalClusterVariables, ParquetRenewableClusterVariables, ParquetShortTermStorageVariables)


def file_mapping_to_parquet_cluster_vars(
        mapping: dict[str, list[FileVariable]],
        var_indices: dict[VariableDescription, int],
        cls: Type[U],
) -> list[],  list[U]:
    """
    Transforms the input mapping into a list of "parquet variables", populating the list of variables and
    their indices along the way.
    """
    res: list[U] = []
    for element_id, vars in mapping.items():
        # more complex here, we need to group by cluster, which is the variable name
        for cluster_id, cluster_variables in groupby(vars, lambda v: v.name):
            local_var_indices: list[int] = []
            for v in vars:
                original_var_desc = v.variable
                var_desc = VariableDescription(name=original_var_desc.unit, unit="", stat=original_var_desc.stat)
                if var_desc in var_indices:
                    local_var_indices.append(var_indices[var_desc])
                else:
                    var_count = len(var_indices)
                    local_var_indices.append(var_count)
                    var_indices[var_desc] = var_count
            parquet_vars = cls(element_id, cluster_id, local_var_indices)
            res.append(parquet_vars)
    return res


def parse_variables_metadata(output_dir: Path) -> tuple[FileMappings, ParquetVariablesMetadata]:
    """
    Builds parquet storage metadata from the actual file study data.
    """
    output = McIndFileOutput(output_dir)
    variable_mappings = get_mappings(output)

    var_indices: dict[VariableDescription, int] = {}

    area_variables = file_mapping_to_parquet_vars(
        variable_mappings.area_values_mappings,
        var_indices,
        ParquetAreaVariables,
    )

    # TODO: link "name" handling
    link_variables = file_mapping_to_parquet_vars(
        variable_mappings.link_values_mappings,
        var_indices,
        ParquetLinkVariables,
    )

    thermal_cluster_variables = file_mapping_to_parquet_cluster_vars(
        variable_mappings.area_details_mappings, var_indices, ParquetThermalClusterVariables
    )
    renewable_cluster_variables = file_mapping_to_parquet_cluster_vars(
        variable_mappings.area_details_res_mappings, var_indices, ParquetRenewableClusterVariables
    )
    sts_variables = file_mapping_to_parquet_cluster_vars(
        variable_mappings.area_details_mappings, var_indices, ParquetShortTermStorageVariables
    )

    return variable_mappings, ParquetVariablesMetadata(
        mc_ind_variables=var_indices,
        mc_all_variables=var_indices,  # TODO
        area_variables=area_variables,
        link_variables=link_variables,
        thermal_cluster_variables=thermal_cluster_variables,
        renewable_cluster_variables=renewable_cluster_variables,
        short_term_storage_variables=sts_variables,
    )


def get_variables_metadata(study_id: str, output_id: str) -> OutputVariablesList:
    session: Session = db.session
    select_vars = select(OUTPUT_VARIABLES_TABLE.c.variables).where(
        OUTPUT_VARIABLES_TABLE.c.study_id == study_id,
        OUTPUT_VARIABLES_TABLE.c.output_id == output_id,
    )
    serialized_vars = session.execute(select_vars).scalars().one()
    parquet_vars = ParquetVariablesMetadata.model_validate_json(serialized_vars)
    return _convert_parquet_variables_metadata(parquet_vars)
