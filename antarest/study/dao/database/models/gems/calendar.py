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

from sqlalchemy import Column, ForeignKeyConstraint, LargeBinary, PrimaryKeyConstraint, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

GEMS_CALENDAR_TABLE = Table(
    "gems_calendar",
    metadata,
    study_data_id_col(),
    Column("calendar", LargeBinary(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id"],
        ["study_data.study_data_id"],
        name="fk_gems_calendar_study_data",
        ondelete="CASCADE",
    ),
    PrimaryKeyConstraint("study_data_id", name="pk_gems_calendar"),
)
