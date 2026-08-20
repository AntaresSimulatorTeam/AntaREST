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
from typing import Any, Iterable, Literal, TypeAlias

from sqlalchemy import BigInteger, Dialect, ForeignKeyConstraint, SmallInteger, String, select, types
from sqlalchemy.orm import Mapped, Session, mapped_column
from typing_extensions import override

from antarest.dbmodel import Base
from antarest.output.filestudy.model import VariableDescription

ElementType: TypeAlias = Literal[
    "area",
    "link",
    "binding_constraint",
    "thermal_cluster",
    "renewable_cluster",
    "short_term_storage",
]

ScenarioAggregation: TypeAlias = Literal["mc-ind", "mc-all"]


class DbParquetOutput(Base):
    # TODO: we should merge the existing v2_output_metadata tables into this one

    __tablename__ = "parquet_output"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class DbParquetVariable(Base):
    __tablename__ = "parquet_variable"

    __table_args__ = (ForeignKeyConstraint(["output_id"], ["parquet_output.id"]),)  # TODO

    output_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scenario_aggregation: Mapped[ScenarioAggregation] = mapped_column(primary_key=True)
    element_type: Mapped[ElementType] = mapped_column(primary_key=True)
    column: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str]
    unit: Mapped[str | None]
    statistic_type: Mapped[str | None]


class Columns(types.TypeDecorator[list[int]]):
    """
    Stores a list of columns as a comma separated string.

    Avoids a many to many relationship which would not be useful.
    """

    impl = String
    cache_ok = True

    @override
    def process_bind_param(self, value: list[int] | None, dialect: Dialect) -> str:
        if not isinstance(value, list):
            raise ValueError("Expected a list of int for variable columns")
        return ",".join(str(c) for c in value)

    @override
    def process_result_value(self, value: Any | None, dialect: Dialect) -> list[int]:
        if not isinstance(value, str):
            raise ValueError("Expected a string in variable columns.")
        return [int(c) for c in value.split(",")]


class DbParquetArea(Base):
    __tablename__ = "parquet_area"

    __table_args__ = ForeignKeyConstraint(["output_id"], ["parquet_output.id"])  # TODO

    output_id: Mapped[int] = mapped_column(BigInteger)
    area_id: Mapped[str]
    mc_all_vars: Mapped[list[int]] = mapped_column(Columns)
    mc_ind_vars: Mapped[list[int]] = mapped_column(Columns)


class VariablesIndex:
    def __init__(self, variables: Iterable[DbParquetVariable]) -> None:
        self._variables: dict[tuple[ScenarioAggregation, ElementType], list[VariableDescription]] = {}
        for v in variables:
            self._variables.setdefault((v.scenario_aggregation, v.element_type), []).append(to_var_model(v))

    def get_variables(self, aggregation: ScenarioAggregation, element_type: ElementType) -> list[VariableDescription]:
        return self._variables.get((aggregation, element_type), [])


def to_var_model(db_var: DbParquetVariable) -> VariableDescription:
    return VariableDescription(db_var.name, db_var.unit, db_var.statistic_type)


def get_area_variables(
    session: Session, output_id: int, aggregation: ScenarioAggregation, area_id: str
) -> list[VariableDescription]:

    # All variables, should load fast ?
    output_variables = session.execute(
        select(DbParquetVariable).where(DbParquetVariable.output_id == output_id)
    ).scalars()
    variables_index = VariablesIndex(output_variables)

    # Get area information
    area = session.execute(select(DbParquetArea).where(DbParquetArea.area_id == area_id)).scalar_one()

    all_areas_vars = variables_index.get_variables(aggregation, "area")
    cols = area.mc_all_vars if aggregation == "mc-all" else area.mc_ind_vars
    return [all_areas_vars[c] for c in cols]
