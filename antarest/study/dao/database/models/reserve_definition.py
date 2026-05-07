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

from sqlalchemy import Column, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.reserve_definition_model import ReserveType
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

RESERVE_DEFINITION_TABLE = Table(
    "reserve_definition",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("reserve_id", String(255), nullable=False, primary_key=True),
    Column("type", enum_col(ReserveType), nullable=False),
    Column("failure_cost", Float, nullable=False),
    Column("spillage_cost", Float, nullable=False),
    Column("reference_activation_duration", Integer, nullable=False),
    Column("power_activation_ratio", Float, nullable=False),
    Column("energy_activation_ratio", Float, nullable=False),
    ForeignKeyConstraint(["study_id", "area_id"], ["area.study_id", "area.area_id"], ondelete="CASCADE"),
)
