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
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import Column, String, Table, select
from sqlalchemy.orm import Session

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


def parse_variables_metadata(output_dir: Path) -> ParquetVariablesMetadata:
    """
    Builds parquet storage metadata from the actual file study data.
    """
    mode_dir = find_mode_dir(output_dir)
    mc_ind_dir = mode_dir / "mc-ind"

    # Any year is representative of the variables for all other years
    first_year_dir = find_first_year_dir(mc_ind_dir)

    # We may have different "frequencies" depending on the areas and links
    # but for a given area or link, we'll have the same variables for all "frequencies"
    # Therefore, we only need to identify variables for one of those frequencies

    for area_dir in first_year_dir.iterdir():
        area_id = area_dir.name

    output_files = identify_mc_ind_files(
        output_dir, MCIndAreasQueryFile.VALUES, MatrixFrequency.HOURLY, [], mc_years=[]
    )
    start_col = get_start_column(MatrixFrequency.HOURLY)
    var_count: int = 0
    var_indices: dict[VariableDescription, int] = {}

    area_variables: list[ParquetAreaVariables] = []
    for f in output_files:
        with open(f.path, "r", encoding="utf-8") as file:
            vars_desc = parse_headers(file, start_col)

        # build variables list for that element
        local_var_indices: list[int] = []
        for v in vars_desc:
            if v in var_indices:
                local_var_indices.append(var_indices[v])
            else:
                local_var_indices.append(var_count)
                var_indices[v] = var_count
                var_count += 1
        parquet_vars = ParquetAreaVariables(area_id=f.location, variables=local_var_indices)
        area_variables.append(parquet_vars)

    return var_indices


def get_variables_metadata(study_id: str, output_id: str) -> OutputVariablesList:
    session: Session = db.session
    select_vars = select(OUTPUT_VARIABLES_TABLE.c.variables).where(
        OUTPUT_VARIABLES_TABLE.c.study_id == study_id,
        OUTPUT_VARIABLES_TABLE.c.output_id == output_id,
    )
    serialized_vars = session.execute(select_vars).scalars().one()
    parquet_vars = ParquetVariablesMetadata.model_validate_json(serialized_vars)
    return _convert_parquet_variables_metadata(parquet_vars)
