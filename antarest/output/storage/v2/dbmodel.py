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

from sqlalchemy import Boolean, Dialect, ForeignKey, Integer, String, UniqueConstraint, types
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from antarest.core.persistence import Base

ElementType: TypeAlias = Literal[
    "area",
    "link",
    "thermal_cluster",
    "renewable_cluster",
    "short_term_storage",
    "binding_constraint",
    "area_id",
    "link_id",
]
ScenarioAggregation: TypeAlias = Literal["mc-ind", "mc-all"]


class IntList(types.TypeDecorator[list[int]]):
    """Compact ordered column indices; an empty list is a valid value."""

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
            raise ValueError("Expected a string")
        return [int(c) for c in value.split(",")] if value else []


class DbOutputMetadataV2(Base):
    __tablename__ = "output_v2_metadata"

    __table_args__ = (UniqueConstraint("study_id", "output_name", name="uq_output_v2_study_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mc_years: Mapped[list[int]] = mapped_column(IntList, default=list)
    metadata_version: Mapped[int] = mapped_column(Integer, default=0)

    # Design note: we don't enforce a foreign key constraint on study_id because it
    #              constrains too much the workflow, for example it does not allow
    #              to mark an output for deletion and delete it later, or just to
    #              delete output after deleting the study itself
    study_id: Mapped[str] = mapped_column(
        String(),
        nullable=False,
    )
    output_name: Mapped[str] = mapped_column(String(), nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    # TODO: enum ?
    mode: Mapped[str] = mapped_column(String(), nullable=False)
    synthesis: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    by_year: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    nb_years: Mapped[int] = mapped_column(Integer(), nullable=False)

    # Definition of the 12-month range
    # TODO: enum
    start_month: Mapped[int] = mapped_column(Integer(), nullable=False)
    # TODO: enum
    january_first_weekday: Mapped[int] = mapped_column(Integer(), nullable=False)
    leap_year: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    # Definition of the simulation range
    start_day: Mapped[int] = mapped_column(Integer(), nullable=False)
    end_day: Mapped[int] = mapped_column(Integer(), nullable=False)

    # For weekly aggregation
    # TODO: enum
    first_weekday: Mapped[int] = mapped_column(Integer(), nullable=False)


class DbParquetVariable(Base):
    """Source of truth for variable columns, excluding the leading index columns."""

    __tablename__ = "parquet_variable"
    output_id: Mapped[int] = mapped_column(ForeignKey("output_v2_metadata.id", ondelete="CASCADE"), primary_key=True)
    scenario_aggregation: Mapped[ScenarioAggregation] = mapped_column(String(16), primary_key=True)
    element_type: Mapped[ElementType] = mapped_column(String(32), primary_key=True)
    column: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    statistic_type: Mapped[str | None] = mapped_column(String)


class ElementColumns:
    """Membership for an actual source file, including its column order.

    Frequency and year distinguish missing files and differences between scenarios.
    positions restores the original interleaving of cluster columns on download.
    """

    output_id: Mapped[int] = mapped_column(
        ForeignKey("output_v2_metadata.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    scenario_aggregation: Mapped[ScenarioAggregation] = mapped_column(String(16), primary_key=True)
    element_type: Mapped[ElementType] = mapped_column(String(32), primary_key=True)
    frequency: Mapped[str] = mapped_column(String(16), primary_key=True)
    mc_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    columns: Mapped[list[int]] = mapped_column(IntList)
    positions: Mapped[list[int]] = mapped_column(IntList)


class DbParquetArea(ElementColumns, Base):
    __tablename__ = "parquet_area"
    area_id: Mapped[str] = mapped_column(String, primary_key=True)


class DbParquetLink(ElementColumns, Base):
    __tablename__ = "parquet_link"
    area_1_id: Mapped[str] = mapped_column(String, primary_key=True)
    area_2_id: Mapped[str] = mapped_column(String, primary_key=True)


class DbParquetCluster(ElementColumns, Base):
    # Cluster families share identifiers; element_type distinguishes their namespaces.
    __tablename__ = "parquet_cluster"
    area_id: Mapped[str] = mapped_column(String, primary_key=True)
    cluster_id: Mapped[str] = mapped_column(String, primary_key=True)


class DbParquetBindingConstraint(ElementColumns, Base):
    __tablename__ = "parquet_binding_constraint"
    constraint_id: Mapped[str] = mapped_column(String, primary_key=True)


ELEMENT_TABLES = (DbParquetArea, DbParquetLink, DbParquetCluster, DbParquetBindingConstraint)
