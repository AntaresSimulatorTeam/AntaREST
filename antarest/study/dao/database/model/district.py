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

from sqlalchemy import Boolean, Column, Enum, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.district_model import DistrictApplyFilter

metadata = Base.metadata

DISTRICT_TABLE = Table(
    "district",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("district_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("output", Boolean, nullable=False),
    Column("comments", String(500), nullable=False),
    Column("apply_filter", Enum(DistrictApplyFilter), nullable=False),
    Column("add_areas", String, nullable=False),
    Column("subtract_areas", String, nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["study.id"],
        ondelete="CASCADE",
    ),
)
