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

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Table, UniqueConstraint

from antarest.dbmodel import Base

metadata = Base.metadata

# Default layer ID constant
DEFAULT_LAYER_ID = "0"

area = Table(
    "area",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("study_id", String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("area_id", String(255), nullable=False),
    Column("area_name", String(255), nullable=False),
    UniqueConstraint("study_id", "area_id", name="uq_area_study_id_area_id"),
)

# Relation: One area can have multiple UI configurations (one per layer)
area_ui = Table(
    "area_ui",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("area_id", Integer, ForeignKey("area.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("layer_id", String(10), nullable=False, default=DEFAULT_LAYER_ID),
    Column("x", Integer, nullable=False, default=0),
    Column("y", Integer, nullable=False, default=0),
    Column("color_r", Integer, nullable=False, default=230),
    Column("color_g", Integer, nullable=False, default=108),
    Column("color_b", Integer, nullable=False, default=44),
    UniqueConstraint("area_id", "layer_id", name="uq_area_ui_area_id_layer_id"),
    Index("ix_area_ui_layer_id", "layer_id"),
)
