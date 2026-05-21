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

from dataclasses import dataclass
from typing import Any, NewType, TypeAlias, TypeVar

from sqlalchemy import Column, Enum, ForeignKeyConstraint, Integer, String, Table, UniqueConstraint, select
from sqlalchemy.orm import Session

from antarest.core.utils.dict_utils import _group_by, _group_by_2
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.output.model import (
    AreaAndLinkVariables,
    AreaClusterVariables,
    AreaVariables,
    McAllVar,
    McIndVar,
    OutputVariablesList,
)

metadata = Base.metadata


OUTPUT_VARIABLES_TABLE = Table(
    "output_v2_variable_defs",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("id", Integer, primary_key=True),  # an integer ID inside the output
    Column("type", Enum("mc-ind", "mc-all"), nullable=False),  # enum mc-ind ou mc-all
    Column("name", String, nullable=False),
    Column("unit", String, nullable=False),
    Column("stat", String, nullable=True),  # enum ?
    Column("column", Integer, nullable=False),
    ForeignKeyConstraint(
        columns=("study_id", "output_id"),
        refcolumns=("output_v2_metadata.study_id", "output_v2_metadata.output_name"),
        name="fk_output_v2_variable_defs_output_v2_metadata",
        ondelete="CASCADE",
    ),
    UniqueConstraint("study_id", "output_id", "type", "name", "unit", "stat", name="uq_output_v2_variable_defs"),
)

# 1 to many relation between an area and a variable
AREA_VARIABLES_TABLE = Table(
    "area_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("area_id", String, primary_key=True),
    Column("variable_id", Integer, primary_key=True),
    ForeignKeyConstraint(
        columns=("study_id", "output_id", "variable_id"),
        refcolumns=(
            "output_v2_variable_defs.study_id",
            "output_v2_variable_defs.output_id",
            "output_v2_variable_defs.id",
        ),
        name="fk_area_variables_output_v2_variable_defs",
        ondelete="CASCADE",
    ),
)

# 1 to many relation between a thermal cluster and a variable
THERMAL_CLUSTER_VARIABLES_TABLE = Table(
    "th_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("area_id", String, primary_key=True),
    Column("cluster_id", String, primary_key=True),
    Column("variable_id", Integer, primary_key=True),
    ForeignKeyConstraint(
        columns=("study_id", "output_id", "variable_id"),
        refcolumns=(
            "output_v2_variable_defs.study_id",
            "output_v2_variable_defs.output_id",
            "output_v2_variable_defs.id",
        ),
        name="fk_th_variables_output_v2_variable_defs",
        ondelete="CASCADE",
    ),
)
# 1 to many relation between a thermal cluster and a variable
RENEWABLE_CLUSTER_VARIABLES_TABLE = Table(
    "re_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("area_id", String, primary_key=True),
    Column("cluster_id", String, primary_key=True),
    Column("variable_id", Integer, primary_key=True),
    ForeignKeyConstraint(
        columns=("study_id", "output_id", "variable_id"),
        refcolumns=(
            "output_v2_variable_defs.study_id",
            "output_v2_variable_defs.output_id",
            "output_v2_variable_defs.id",
        ),
        name="fk_re_variables_output_v2_variable_defs",
        ondelete="CASCADE",
    ),
)

# 1 to many relation between a thermal cluster and a variable
SHORT_TERM_STORAGE_VARIABLES_TABLE = Table(
    "sts_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("area_id", String, primary_key=True),
    Column("cluster_id", String, primary_key=True),
    Column("variable_id", Integer, primary_key=True),
    ForeignKeyConstraint(
        columns=("study_id", "output_id", "variable_id"),
        refcolumns=(
            "output_v2_variable_defs.study_id",
            "output_v2_variable_defs.output_id",
            "output_v2_variable_defs.id",
        ),
        name="fk_sts_variables_output_v2_variable_defs",
        ondelete="CASCADE",
    ),
)


AreaId = NewType("AreaId", str)
ClusterId = NewType("ClusterId", str)
VariableId = NewType("VariableId", int)

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def _get_variables(study_id: str, output_id: str) -> dict[VariableId, McIndVar | McAllVar]:
    """
    Reads all output variables for that output, identified by their id

    # TODO: retrieve column information altogether
    """
    session: Session = db.session
    select_vars = select(OUTPUT_VARIABLES_TABLE).where(
        OUTPUT_VARIABLES_TABLE.c.study_id == study_id,
        OUTPUT_VARIABLES_TABLE.c.output_id == output_id,
    )
    var_rows = session.execute(select_vars)
    variables: dict[VariableId, McIndVar | McAllVar] = {}
    for row in var_rows:
        variable_id = row.id
        match row.type:
            case "mc-ind":
                variables[variable_id] = McIndVar(name=row.name, unit=row.unit)
            case "mc-all":
                variables[variable_id] = McAllVar(name=row.name, unit=row.unit, stat=row.stat)
    return variables


def _get_area_variables(
    study_id: str, output_id: str, variables: dict[VariableId, McIndVar | McAllVar]
) -> dict[AreaId, list[McIndVar | McAllVar]]:
    session: Session = db.session
    select_areas = select(AREA_VARIABLES_TABLE).where(
        AREA_VARIABLES_TABLE.c.study_id == study_id,
        AREA_VARIABLES_TABLE.c.output_id == output_id,
    )
    return _group_by(
        data=session.execute(select_areas), key=lambda row: row.area_id, value=lambda row: variables[row.variable_id]
    )


def _get_cluster_variables(
    study_id: str,
    output_id: str,
    table: Table,
    variables: dict[VariableId, McIndVar | McAllVar],
) -> dict[AreaId, dict[ClusterId, list[McIndVar | McAllVar]]]:
    """Reads all cluster-level variable assignments from the given junction table."""
    session: Session = db.session
    query = select(table).where(
        table.c.study_id == study_id,
        table.c.output_id == output_id,
    )
    return _group_by_2(
        data=session.execute(query),
        key1=lambda row: row.area_id,
        key2=lambda row: row.cluster_id,
        value=lambda row: variables[row.variable_id],
    )


def _build_cluster_variables_list(
    cluster_map: dict[ClusterId, list[McIndVar | McAllVar]],
    var_type: type,
) -> list[AreaClusterVariables[list[McIndVar | McAllVar]]]:
    """Builds a list of AreaClusterVariables, keeping only variables of the given type."""
    return [
        AreaClusterVariables(
            name=cluster_id,
            variables=[v for v in cluster_vars if isinstance(v, var_type)],
        )
        for cluster_id, cluster_vars in cluster_map.items()
    ]


def _build_area_variables(
    area_id: AreaId,
    area_vars: dict[AreaId, list[McIndVar | McAllVar]],
    th_vars: dict[AreaId, dict[ClusterId, list[McIndVar | McAllVar]]],
    re_vars: dict[AreaId, dict[ClusterId, list[McIndVar | McAllVar]]],
    sts_vars: dict[AreaId, dict[ClusterId, list[McIndVar | McAllVar]]],
    var_type: type,
) -> AreaVariables[list[McIndVar | McAllVar]]:
    """Builds an AreaVariables for a single area, filtered to the given variable type."""
    return AreaVariables(
        name=area_id,
        variables=[v for v in area_vars.get(area_id, []) if isinstance(v, var_type)],
        thermal_clusters=_build_cluster_variables_list(th_vars.get(area_id, {}), var_type),
        renewable_clusters=_build_cluster_variables_list(re_vars.get(area_id, {}), var_type),
        short_term_storages=_build_cluster_variables_list(sts_vars.get(area_id, {}), var_type),
    )


@dataclass(frozen=True)
class VarKey:
    type: str
    name: str
    unit: str | None
    stat: str | None


def _var_key(var: McIndVar | McAllVar) -> VarKey:
    if isinstance(var, McIndVar):
        return VarKey(type="mc-ind", name=var.name, unit=var.unit, stat=None)
    return VarKey(type="mc-all", name=var.name, unit=var.unit, stat=var.stat)


_Row: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class _VariableRows:
    variable_rows: list[_Row]
    area_rows: list[_Row]
    th_rows: list[_Row]
    re_rows: list[_Row]
    sts_rows: list[_Row]


def _variables_list_to_rows(
    study_id: str,
    output_id: str,
    variables_list: OutputVariablesList,
) -> _VariableRows:
    """
    Walks the OutputVariablesList tree and returns the rows to insert into each table.

    Variables are deduplicated by (type, name, unit, stat). A sequential integer ID is
    assigned to each unique variable and used as the foreign key in all junction tables.
    Junction rows are also deduplicated so the same (area, variable) pair is not inserted twice.
    """
    var_id_by_key: dict[VarKey, VariableId] = {}

    def get_or_register_variable(var: McIndVar | McAllVar) -> VariableId:
        key = _var_key(var)
        if key not in var_id_by_key:
            var_id_by_key[key] = VariableId(len(var_id_by_key))
        return var_id_by_key[key]

    # Use sets of tuples to naturally deduplicate junction rows
    area_pairs: set[tuple[str, VariableId]] = set()
    th_triples: set[tuple[str, str, VariableId]] = set()
    re_triples: set[tuple[str, str, VariableId]] = set()
    sts_triples: set[tuple[str, str, VariableId]] = set()

    def register_area(area: AreaVariables[Any]) -> None:
        for var in area.variables:
            area_pairs.add((area.name, get_or_register_variable(var)))

        for cluster_table, clusters in [
            (th_triples, area.thermal_clusters),
            (re_triples, area.renewable_clusters),
            (sts_triples, area.short_term_storages),
        ]:
            for cluster in clusters:
                for var in cluster.variables:
                    cluster_table.add((area.name, cluster.name, get_or_register_variable(var)))

    all_areas: list[AreaVariables[Any]] = [*variables_list.mc_ind.areas, *variables_list.mc_all.areas]
    for area in all_areas:
        register_area(area)

    base = {"study_id": study_id, "output_id": output_id}

    variable_rows = [
        {
            **base,
            "id": var_id,
            "type": key.type,
            "name": key.name,
            "unit": key.unit,
            "stat": key.stat,
            "column": var_id,
        }
        for key, var_id in var_id_by_key.items()
    ]
    area_rows = [{**base, "area_id": area_id, "variable_id": var_id} for area_id, var_id in area_pairs]
    th_rows = [
        {**base, "area_id": area_id, "cluster_id": cluster_id, "variable_id": var_id}
        for area_id, cluster_id, var_id in th_triples
    ]
    re_rows = [
        {**base, "area_id": area_id, "cluster_id": cluster_id, "variable_id": var_id}
        for area_id, cluster_id, var_id in re_triples
    ]
    sts_rows = [
        {**base, "area_id": area_id, "cluster_id": cluster_id, "variable_id": var_id}
        for area_id, cluster_id, var_id in sts_triples
    ]

    return _VariableRows(
        variable_rows=variable_rows,
        area_rows=area_rows,
        th_rows=th_rows,
        re_rows=re_rows,
        sts_rows=sts_rows,
    )


def save_variables_metadata(study_id: str, output_id: str, variables_list: OutputVariablesList) -> None:
    """Writes an OutputVariablesList to the database tables.

    Inserts all unique variables into OUTPUT_VARIABLES_TABLE, then populates the four
    junction tables (areas, thermal clusters, renewable clusters, short-term storages)
    with the variable assignments for each object in the study.
    """
    session: Session = db.session

    rows = _variables_list_to_rows(study_id, output_id, variables_list)

    if rows.variable_rows:
        session.execute(OUTPUT_VARIABLES_TABLE.insert(), rows.variable_rows)
    if rows.area_rows:
        session.execute(AREA_VARIABLES_TABLE.insert(), rows.area_rows)
    if rows.th_rows:
        session.execute(THERMAL_CLUSTER_VARIABLES_TABLE.insert(), rows.th_rows)
    if rows.re_rows:
        session.execute(RENEWABLE_CLUSTER_VARIABLES_TABLE.insert(), rows.re_rows)
    if rows.sts_rows:
        session.execute(SHORT_TERM_STORAGE_VARIABLES_TABLE.insert(), rows.sts_rows)


def get_variables_metadata(study_id: str, output_id: str) -> OutputVariablesList:
    variables = _get_variables(study_id, output_id)

    area_vars = _get_area_variables(study_id, output_id, variables)
    th_vars = _get_cluster_variables(study_id, output_id, THERMAL_CLUSTER_VARIABLES_TABLE, variables)
    re_vars = _get_cluster_variables(study_id, output_id, RENEWABLE_CLUSTER_VARIABLES_TABLE, variables)
    sts_vars = _get_cluster_variables(study_id, output_id, SHORT_TERM_STORAGE_VARIABLES_TABLE, variables)

    all_area_ids = sorted(set(area_vars) | set(th_vars) | set(re_vars) | set(sts_vars))

    def build_areas_for_type(var_type: type) -> list[AreaVariables[list[McIndVar | McAllVar]]]:
        return [
            _build_area_variables(area_id, area_vars, th_vars, re_vars, sts_vars, var_type) for area_id in all_area_ids
        ]

    return OutputVariablesList(
        mc_ind=AreaAndLinkVariables(areas=build_areas_for_type(McIndVar), links=[]),
        mc_all=AreaAndLinkVariables(areas=build_areas_for_type(McAllVar), links=[]),
    )
