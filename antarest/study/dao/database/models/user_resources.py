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
SQLAlchemy Core table definitions for user resources storage.
"""

from sqlalchemy import Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.user_model import ResourceType
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

_RESOURCE_TYPE_ENUM = enum_col(ResourceType, name="resourcetype")

USER_RESOURCES_TABLE = Table(
    "user_resources",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("path", String(255), nullable=False, primary_key=True),
    Column("resource_type", _RESOURCE_TYPE_ENUM, nullable=False),
    Column("blob_id", String(64), nullable=True),
    ForeignKeyConstraint(["study_id"], ["study_data_container.study_data_id"], ondelete="CASCADE"),
)
