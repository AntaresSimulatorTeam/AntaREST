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

from sqlalchemy import Column, ForeignKeyConstraint, PrimaryKeyConstraint, String, Table, Text

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

GEMS_DATA_SERIES_TABLE = Table(
    "gems_data_series",
    Base.metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    # SQL has no portable array/matrix column type (PostgreSQL's `ARRAY` isn't supported by SQLite),
    # so the series is stored as text and (de)serialized to/from a numpy array in the DAO.
    Column("values", Text(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id"], ["study_data.study_data_id"], name="fk_gems_data_series_study_data", ondelete="CASCADE"
    ),
    PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_data_series"),
)
