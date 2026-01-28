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
SQLAlchemy Core table definitions for database-based study storage.

This module defines the database tables used when a study has storage_mode=DATABASE.
These tables store study data (areas, UI positions, etc.) in the database instead of the filesystem.
"""

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, ForeignKeyConstraint, Integer, String, Table
from sqlalchemy.sql.schema import SchemaItem

from antarest.dbmodel import Base
from antarest.study.business.model.area_properties_model import AdequacyPatchMode

metadata = Base.metadata

AREA_TABLE = Table(
    "area",
    metadata,
    Column("study_id", String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("area_name", String(255), nullable=False),
    Column("energy_cost_unsupplied", Float, nullable=False),
    Column("energy_cost_spilled", Float, nullable=False),
    Column("non_dispatch_power", Boolean, nullable=False),
    Column("dispatch_hydro_power", Boolean, nullable=False),
    Column("other_dispatch_power", Boolean, nullable=False),
    Column("spread_unsupplied_energy_cost", Float, nullable=False),
    Column("spread_spilled_energy_cost", Float, nullable=False),
    Column("filter_synthesis", String(), nullable=False),
    Column("filter_by_year", String(), nullable=False),
    Column("adequacy_patch_mode", Enum(AdequacyPatchMode), nullable=True),  # Since v8.3
)

# Relation: One area can have multiple UI configurations (one per layer)
AREA_UI_TABLE = Table(
    "area_ui",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("layer_id", String(10), nullable=False, primary_key=True),
    Column("x", Integer, nullable=False),
    Column("y", Integer, nullable=False),
    Column("color_r", Integer, nullable=False),
    Column("color_g", Integer, nullable=False),
    Column("color_b", Integer, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id"],
        ["area.study_id", "area.area_id"],
        ondelete="CASCADE",
    ),
)


def _get_args() -> list[SchemaItem]:
    return [
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("matrix_id", String(64), nullable=False),
        ForeignKeyConstraint(["study_id", "area_id"], ["area.study_id", "area.area_id"], ondelete="CASCADE"),
    ]


# Relation: One to one with `AREA_TABLE`
LOAD_TABLE = Table("load", metadata, *_get_args())
SOLAR_TABLE = Table("solar", metadata, *_get_args())
WIND_TABLE = Table("wind", metadata, *_get_args())
RESERVES_TABLE = Table("reserves", metadata, *_get_args())
MISC_GEN_TABLE = Table("misc_gen", metadata, *_get_args())
