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

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

AREA_TABLE = Table(
    "area",
    metadata,
    Column("study_id", String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("area_name", String(255), nullable=False),
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
