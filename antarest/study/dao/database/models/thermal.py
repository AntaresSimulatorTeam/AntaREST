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
SQLAlchemy Core table definitions for thermal cluster storage.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.thermal_cluster_model import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCostGeneration,
)
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

_GEN_TS_ENUM = enum_col(LocalTSGenerationBehavior, name="localtsgenerationbehavior")
_LAW_OPTION_ENUM = enum_col(LawOption, name="lawoption")
_COST_GEN_ENUM = enum_col(ThermalCostGeneration, name="thermalcostgeneration")

THERMAL_CLUSTER_TABLE = Table(
    "thermal_cluster",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("thermal_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("unit_count", Integer, nullable=False),
    Column("nominal_capacity", Float, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("group", String(255), nullable=False),
    Column("gen_ts", _GEN_TS_ENUM, nullable=False),
    Column("min_stable_power", Float, nullable=False),
    Column("min_up_time", Integer, nullable=False),
    Column("min_down_time", Integer, nullable=False),
    Column("must_run", Boolean, nullable=False),
    Column("spinning", Float, nullable=False),
    Column("volatility_forced", Float, nullable=False),
    Column("volatility_planned", Float, nullable=False),
    Column("law_forced", _LAW_OPTION_ENUM, nullable=False),
    Column("law_planned", _LAW_OPTION_ENUM, nullable=False),
    Column("marginal_cost", Float, nullable=False),
    Column("spread_cost", Float, nullable=False),
    Column("fixed_cost", Float, nullable=False),
    Column("startup_cost", Float, nullable=False),
    Column("market_bid_cost", Float, nullable=False),
    Column("co2", Float, nullable=False),
    Column("nh3", Float, nullable=True),
    Column("so2", Float, nullable=True),
    Column("nox", Float, nullable=True),
    Column("pm2_5", Float, nullable=True),
    Column("pm5", Float, nullable=True),
    Column("pm10", Float, nullable=True),
    Column("nmvoc", Float, nullable=True),
    Column("op1", Float, nullable=True),
    Column("op2", Float, nullable=True),
    Column("op3", Float, nullable=True),
    Column("op4", Float, nullable=True),
    Column("op5", Float, nullable=True),
    Column("cost_generation", _COST_GEN_ENUM, nullable=True),
    Column("efficiency", Float, nullable=True),
    Column("variable_o_m_cost", Float, nullable=True),
    ForeignKeyConstraint(["study_id", "area_id"], ["area.study_id", "area.area_id"], ondelete="CASCADE"),
)


def _create_thermal_matrix_table(name: str) -> Table:
    return Table(
        name,
        metadata,
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("thermal_id", String(255), nullable=False, primary_key=True),
        Column("matrix_id", String(64), nullable=False),
        ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            ondelete="CASCADE",
        ),
    )


THERMAL_PREPRO_TABLE = _create_thermal_matrix_table("thermal_prepro")
THERMAL_MODULATION_TABLE = _create_thermal_matrix_table("thermal_modulation")
THERMAL_SERIES_TABLE = _create_thermal_matrix_table("thermal_series")
THERMAL_FUEL_COST_TABLE = _create_thermal_matrix_table("thermal_fuel_cost")
THERMAL_CO2_COST_TABLE = _create_thermal_matrix_table("thermal_co2_cost")
