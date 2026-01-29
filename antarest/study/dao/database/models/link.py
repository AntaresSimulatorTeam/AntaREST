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

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.link_model import AssetType, LinkStyle, TransmissionCapacity

metadata = Base.metadata

# Relation: One to many with `AREA_TABLE`: 1 area can have multiple links
LINK_TABLE = Table(
    "link",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("area1", String(length=255), nullable=False),
    Column("area2", String(length=255), nullable=False),
    Column("hurdles_cost", Boolean(), nullable=False),
    Column("loop_flow", Boolean(), nullable=False),
    Column("use_phase_shifter", Boolean(), nullable=False),
    Column("transmission_capacities", Enum(TransmissionCapacity), nullable=False),
    Column("asset_type", Enum(AssetType), nullable=False),
    Column("display_comments", Boolean(), nullable=False),
    Column("comments", String(), nullable=False),
    Column("colorr", Integer(), nullable=False),
    Column("colorb", Integer(), nullable=False),
    Column("colorg", Integer(), nullable=False),
    Column("link_width", Float(), nullable=False),
    Column("link_style", Enum(LinkStyle), nullable=False),
    Column("filter_synthesis", String(), nullable=False),
    Column("filter_year_by_year", String(), nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area1"],
        ["area.study_id", "area.area_id"],
        name="fk_link_study_id_area_id_1",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "area2"],
        ["area.study_id", "area.area_id"],
        name="fk_link_study_id_area_id_2",
        ondelete="CASCADE",
    ),
)
