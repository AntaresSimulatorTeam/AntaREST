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
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

# `BigInteger` alone does not autoincrement on SQLite: only `INTEGER PRIMARY KEY` aliases the
# rowid. The `Integer` variant makes the column an autoincrementing rowid alias there, while
# keeping a real 64 bits column on PostgreSQL.
STUDY_DATA_ID_TYPE = BigInteger().with_variant(Integer, "sqlite")

STUDY_DATA_TABLE = Table(
    "study_data",
    metadata,
    Column("study_data_id", STUDY_DATA_ID_TYPE, primary_key=True, autoincrement=True),
    Column("study_id", String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False, unique=True),
)


def study_data_id_col(*, primary_key: bool = True) -> Column[int]:
    """
    The surrogate study key carried by every study data table.

    It replaces the 36 chars `study_id` as the leading column of the composite primary keys,
    and ultimately references `study_data.study_data_id`.
    """
    return Column("study_data_id", STUDY_DATA_ID_TYPE, nullable=False, primary_key=primary_key)
