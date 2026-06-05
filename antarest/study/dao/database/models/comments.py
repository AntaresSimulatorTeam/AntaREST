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
SQLAlchemy Core table definitions for study comments storage.
"""

from sqlalchemy import Column, ForeignKeyConstraint, String, Table, Text

from antarest.dbmodel import Base

metadata = Base.metadata

COMMENTS_TABLE = Table(
    "comments",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("comments", Text(), nullable=False, server_default=""),
    ForeignKeyConstraint(["study_id"], ["study_data.study_id"], ondelete="CASCADE"),
)
