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

from sqlalchemy import Boolean, Column, Enum, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.config.general_model import BuildingMode, Month, WeekDay
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode

metadata = Base.metadata

# Relations: One to one with `Study`

GENERAL_SETTINGS_TABLE = Table(
    "link",
    metadata,
    Column("study_id", String(length=36), nullable=False, primary_key=True),
    Column("mode", Enum(Mode), nullable=False),
    Column("first_day", Integer(), nullable=False),
    Column("last_day", Integer(), nullable=False),
    Column("horizon", String(), nullable=False),
    Column("first_month", Enum(Month), nullable=False),
    Column("first_week_day", Enum(WeekDay), nullable=False),
    Column("first_january", Enum(WeekDay), nullable=False),
    Column("leap_year", Boolean(), nullable=False),
    Column("nb_years", Integer(), nullable=False),
    Column("building_mode", Enum(BuildingMode), nullable=False),
    Column("selection_mode", Boolean(), nullable=False),
    Column("year_by_year", Boolean(), nullable=False),
    Column("simulation_synthesis", Boolean(), nullable=False),
    Column("mc_scenario", Boolean(), nullable=False),
    Column("filtering", Boolean(), nullable=True),
    Column("geographic_trimming", Boolean(), nullable=True),
    Column("thematic_trimming", Boolean(), nullable=True),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_general_settings_study_id", ondelete="CASCADE"),
)
