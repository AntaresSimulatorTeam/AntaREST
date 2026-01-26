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
SQLAlchemy Core table definitions for district storage.

This module defines the database tables for districts when a study has storage_mode=DATABASE.
"""

from sqlalchemy import Boolean, Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.district_model import DistrictApplyFilter

metadata = Base.metadata

# Table principale des districts
DISTRICT_TABLE = Table(
    "district",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("district_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("output", Boolean, nullable=False),
    Column("comments", String(500), nullable=False),
    Column("apply_filter", String(50), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["study.id"],
        ondelete="CASCADE",
    ),
)

# Table de jointure pour les areas du district (add_areas et subtract_areas)
DISTRICT_AREA_TABLE = Table(
    "district_area",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("district_id", String(255), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("mode", String(10), nullable=False, primary_key=True),
    ForeignKeyConstraint(
        ["study_id", "district_id"],
        ["district.study_id", "district.district_id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "area_id"],
        ["area.study_id", "area.area_id"],
        ondelete="CASCADE",
    ),
)
