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
SQLAlchemy Core table definitions for scenario builder (ruleset).
"""

from sqlalchemy import JSON, Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata


def _create_area_scenario_table(name: str) -> Table:
    return Table(
        name,
        metadata,
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("value", JSON, nullable=False),
        ForeignKeyConstraint(("study_id", "area_id"), ["area.study_id", "area.area_id"], ondelete="CASCADE"),
    )


SCENARIO_LOAD_TABLE = _create_area_scenario_table("scenario_load")
SCENARIO_HYDRO_TABLE = _create_area_scenario_table("scenario_hydro")
SCENARIO_WIND_TABLE = _create_area_scenario_table("scenario_wind")
SCENARIO_SOLAR_TABLE = _create_area_scenario_table("scenario_solar")
SCENARIO_HYDRO_INITIAL_LEVEL_TABLE = _create_area_scenario_table("scenario_hydro_initial_level")
SCENARIO_HYDRO_FINAL_LEVEL_TABLE = _create_area_scenario_table("scenario_hydro_final_level")
SCENARIO_HYDRO_GENERATION_POWER_TABLE = _create_area_scenario_table("scenario_hydro_generation_power")

SCENARIO_NTC_TABLE = Table(
    "scenario_ntc",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area1", String(255), nullable=False, primary_key=True),
    Column("area2", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area1", "area2"],
        ["link.study_id", "link.area1", "link.area2"],
        ondelete="CASCADE",
    ),
)

SCENARIO_BINDING_CONSTRAINTS_TABLE = Table(
    "scenario_binding_constraints",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("bc_group_id", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(["study_id"], ["study_data.study_id"], ondelete="CASCADE"),
)

SCENARIO_THERMAL_TABLE = Table(
    "scenario_thermal",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("thermal_id", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "thermal_id"],
        ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
        ondelete="CASCADE",
    ),
)

SCENARIO_RENEWABLE_TABLE = Table(
    "scenario_renewable",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("renewable_id", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "renewable_id"],
        ["renewable_cluster.study_id", "renewable_cluster.area_id", "renewable_cluster.renewable_id"],
        ondelete="CASCADE",
    ),
)

SCENARIO_STORAGE_INFLOWS_TABLE = Table(
    "scenario_storage_inflows",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("st_storage_id", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "st_storage_id"],
        ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
        ondelete="CASCADE",
    ),
)

SCENARIO_STORAGE_CONSTRAINTS_TABLE = Table(
    "scenario_storage_constraints",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("st_storage_id", String(255), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("value", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "st_storage_id", "constraint_id"],
        [
            "st_storage_additional_constraint.study_id",
            "st_storage_additional_constraint.area_id",
            "st_storage_additional_constraint.st_storage_id",
            "st_storage_additional_constraint.constraint_id",
        ],
        ondelete="CASCADE",
    ),
)
