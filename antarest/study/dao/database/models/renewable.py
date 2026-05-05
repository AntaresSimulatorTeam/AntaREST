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
SQLAlchemy Core table definitions for renewable cluster storage.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.renewable_cluster_model import TimeSeriesInterpretation
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

_TS_INTERPRETATION_ENUM = enum_col(TimeSeriesInterpretation, name="renewabletsinterpretation")

RENEWABLE_CLUSTER_TABLE = Table(
    "renewable_cluster",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("renewable_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("unit_count", Integer, nullable=False),
    Column("nominal_capacity", Float, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("group", String(255), nullable=False),
    Column("ts_interpretation", _TS_INTERPRETATION_ENUM, nullable=False),
    ForeignKeyConstraint(["study_id", "area_id"], ["area.study_id", "area.area_id"], ondelete="CASCADE"),
)

RENEWABLE_SERIES_TABLE = Table(
    "renewable_series",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("renewable_id", String(255), nullable=False, primary_key=True),
    Column("matrix_id", String(64), nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "renewable_id"],
        ["renewable_cluster.study_id", "renewable_cluster.area_id", "renewable_cluster.renewable_id"],
        ondelete="CASCADE",
    ),
)
