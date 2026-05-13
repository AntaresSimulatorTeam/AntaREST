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

from itertools import groupby
from typing import Callable, Iterable, NewType, TypeVar

from sqlalchemy import Column, Enum, ForeignKeyConstraint, Integer, String, Table, UniqueConstraint, select
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.output.model import McAllVar, McIndVar, OutputVariablesList

metadata = Base.metadata


OUTPUT_VARIABLES_TABLE = Table(
    "output_v2_variables",
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
        name="fk_output_v2_variables_output_v2_metadata",
        ondelete="CASCADE",
    ),
    UniqueConstraint("study_id", "output_id", "type", "name", "unit", "stat", name="uq_output_v2_variables"),
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
        refcolumns=("output_v2_variables.study_id", "output_v2_variables.output_id", "output_v2_variables.id"),
        name="fk_area_variables_output_v2_variables",
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
        refcolumns=("output_v2_variables.study_id", "output_v2_variables.output_id", "output_v2_variables.id"),
        name="fk_th_variables_output_v2_variables",
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
        refcolumns=("output_v2_variables.study_id", "output_v2_variables.output_id", "output_v2_variables.id"),
        name="fk_re_variables_output_v2_variables",
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
        refcolumns=("output_v2_variables.study_id", "output_v2_variables.output_id", "output_v2_variables.id"),
        name="fk_sts_variables_output_v2_variables",
        ondelete="CASCADE",
    ),
)


AreaId = NewType("AreaId", str)
ClusterId = NewType("ClusterId", str)
VariableId = NewType("VariableId", int)


def _get_variables(study_id: str, output_id: str) -> dict[VariableId, McIndVar | McAllVar]:
    """
    Reads all output variables for that output, identified by their id

    # TODO: retrieve column information altogether
    """
    session: Session = db.session
    select_vars = select(OUTPUT_VARIABLES_TABLE).where(
        OUTPUT_VARIABLES_TABLE.c.study_id == study_id and OUTPUT_VARIABLES_TABLE.c.output_id == output_id
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
        AREA_VARIABLES_TABLE.c.study_id == study_id and AREA_VARIABLES_TABLE.c.output_id == output_id
    )
    return _group_by(
        data=session.execute(select_areas), key=lambda row: row.area_id, value=lambda row: variables[row.variable_id]
    )


K = TypeVar("K")
K1 = TypeVar("K1")
K2 = TypeVar("K2")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def _group_by(data: Iterable[T], key: Callable[[T], K], value: Callable[[T], V]) -> dict[K, list[V]]:
    res = {}
    for k, items in groupby(data, key=key):
        res[k] = [value(i) for i in items]
    return res


def _group_by_2(
    data: Iterable[T], key1: Callable[[T], K1], key2: Callable[[T], K2], value: Callable[[T], V]
) -> dict[K1, dict[K2, list[V]]]:
    res = {}
    for k, items in groupby(data, key=key1):
        res[k] = _group_by(items, key=key2, value=value)
    return res


def _get_th_variables(
    study_id: str, output_id: str, variables: dict[VariableId, McIndVar | McAllVar]
) -> dict[AreaId, dict[ClusterId, list[McIndVar | McAllVar]]]:
    session: Session = db.session
    select_areas = select(THERMAL_CLUSTER_VARIABLES_TABLE).where(
        THERMAL_CLUSTER_VARIABLES_TABLE.c.study_id == study_id
        and THERMAL_CLUSTER_VARIABLES_TABLE.c.output_id == output_id
    )
    return _group_by_2(
        data=session.execute(select_areas),
        key1=lambda row: row.area_id,
        key2=lambda row: row.cluster_id,
        value=lambda row: variables[row.variable_id],
    )


def get_variables_metadata(study_id: str, output_id: str) -> OutputVariablesList:
    session: Session = db.session
    variables = _get_variables(study_id, output_id)
    area_variables = _get_area_variables(study_id, output_id, variables)
    th_variables = _get_th_variables(study_id, output_id, variables)

    return OutputVariablesList()
