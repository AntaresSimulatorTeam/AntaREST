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
from typing import Any, Literal, TypeAlias

from sqlalchemy import BigInteger, Dialect, ForeignKeyConstraint, SmallInteger, String, types
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from antarest.dbmodel import Base

ElementType: TypeAlias = Literal[
    "area",
    "link",
    "binding_constraint",
    "thermal_cluster",
    "renewable_cluster",
    "short_term_storage",
]

ScenarioAggregation: TypeAlias = Literal["mc-ind", "mc-all"]


class IntList(types.TypeDecorator[list[int]]):
    """
    Stores a list of integers as a comma separated string.

    Can avoid many to many relationships which would not be useful.
    """

    impl = String
    cache_ok = True

    @override
    def process_bind_param(self, value: list[int] | None, dialect: Dialect) -> str:
        if not isinstance(value, list):
            raise ValueError("Expected a list of int")
        return ",".join(str(c) for c in value)

    @override
    def process_result_value(self, value: Any | None, dialect: Dialect) -> list[int]:
        if not isinstance(value, str):
            raise ValueError("Expected a string.")
        return [int(c) for c in value.split(",")]


class DbParquetOutput(Base):
    # TODO: we should merge the existing v2_output_metadata tables into this one
    #       the integer identifier will be easier and more efficient to use than the couple of strings
    #       study_id / output_id

    __tablename__ = "parquet_output"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mc_years: Mapped[list[int]] = mapped_column(IntList)


class DbParquetVariable(Base):
    """
    Represents one of the variables referenced in an output.

    Those variables are then referenced by elements of the system (areas, links ...), that contain
    actual data for them.

    Attributes:
        column: the column offset in the actual parquet file, compared to index columns (starts at 0).
    """

    __tablename__ = "parquet_variable"

    __table_args__ = (ForeignKeyConstraint(["output_id"], ["parquet_output.id"]),)  # TODO

    output_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scenario_aggregation: Mapped[ScenarioAggregation] = mapped_column(primary_key=True)
    element_type: Mapped[ElementType] = mapped_column(primary_key=True)
    column: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str]
    unit: Mapped[str | None]
    statistic_type: Mapped[str | None]


class DbParquetArea(Base):
    """
    Information related to an area of an output, in particular which variables it has data for,
    in mc-ind and in mc-all (they may differ).

    The variables are reference through their column index.
    """

    __tablename__ = "parquet_area"

    __table_args__ = (ForeignKeyConstraint(["output_id"], ["parquet_output.id"]),)  # TODO

    output_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    area_id: Mapped[str] = mapped_column(primary_key=True)
    mc_all_vars: Mapped[list[int]] = mapped_column(IntList)
    mc_ind_vars: Mapped[list[int]] = mapped_column(IntList)


# TODO: add tables for other element types: links, thermal clusters, etc
