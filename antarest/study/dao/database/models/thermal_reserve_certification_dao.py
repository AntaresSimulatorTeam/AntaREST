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

from sqlalchemy import Column, Float, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

THERMAL_RESERVE_CERTIFICATION_TABLE = Table(
    "thermal_reserve_certifications",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("thermal_id", String(255), nullable=False, primary_key=True),
    Column("reserve_id", String(255), nullable=False, primary_key=True),
    Column("max_power", Float, nullable=False),
    Column("max_power_off", Float, nullable=False),
    Column("participation_cost", Float, nullable=False),
    Column("participation_cost_off", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "thermal_id"],
        ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "area_id", "reserve_id"],
        ["reserve_definition.study_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
        ondelete="CASCADE",
    ),
)