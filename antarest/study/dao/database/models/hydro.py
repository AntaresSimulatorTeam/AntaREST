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
SQLAlchemy Core table definitions for hydro configuration storage.

This module defines the database tables used for storing hydro-related data
when a study has storage_mode=DATABASE.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

HYDRO_MANAGEMENT_TABLE = Table(
    "hydro_management",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    # Hydro management configuration fields
    Column("inter_daily_breakdown", Float, nullable=False),
    Column("intra_daily_modulation", Float, nullable=False),
    Column("inter_monthly_breakdown", Float, nullable=False),
    Column("reservoir", Boolean, nullable=False),
    Column("reservoir_capacity", Float, nullable=False),
    Column("follow_load", Boolean, nullable=False),
    Column("use_water", Boolean, nullable=False),
    Column("hard_bounds", Boolean, nullable=False),
    Column("initialize_reservoir_date", Integer, nullable=False),
    Column("use_heuristic", Boolean, nullable=False),
    Column("power_to_level", Boolean, nullable=False),
    Column("use_leeway", Boolean, nullable=False),
    Column("leeway_low", Float, nullable=False),
    Column("leeway_up", Float, nullable=False),
    Column("pumping_efficiency", Float, nullable=False),
    # v9.2+ field - nullable for older study versions
    Column("overflow_spilled_cost_difference", Float, nullable=True),
    ForeignKeyConstraint(
        ["study_id", "area_id"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_management_study_id_area_id_area",
        ondelete="CASCADE",
    ),
)

HYDRO_INFLOW_STRUCTURE_TABLE = Table(
    "hydro_inflow_structure",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("inter_monthly_correlation", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_inflow_structure_study_id_area_id_area",
        ondelete="CASCADE",
    ),
)

HYDRO_ALLOCATION_TABLE = Table(
    "hydro_allocation",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("source_area_id", String(255), nullable=False, primary_key=True),
    Column("target_area_id", String(255), nullable=False, primary_key=True),
    Column("coefficient", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "source_area_id"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_allocation_study_id_source_area_id_area",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "target_area_id"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_allocation_study_id_target_area_id_area",
        ondelete="CASCADE",
    ),
)

HYDRO_CORRELATION_TABLE = Table(
    "hydro_correlation",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_from", String(255), nullable=False, primary_key=True),
    Column("area_to", String(255), nullable=False, primary_key=True),
    # Stored as -1 to 1
    Column("coefficient", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_from"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_correlation_study_id_area_from_area",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "area_to"],
        ["area.study_id", "area.area_id"],
        name="fk_hydro_correlation_study_id_area_to_area",
        ondelete="CASCADE",
    ),
)
