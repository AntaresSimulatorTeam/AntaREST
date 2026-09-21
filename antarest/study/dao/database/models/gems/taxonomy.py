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
from sqlalchemy import Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

GEMS_TAXONOMY_METADATA_TABLE = Table(
    "gems_taxonomy_metadata",
    metadata,
    study_data_id_col(),
    Column("id", String(255), nullable=False),
    Column("description", String(), nullable=True),
    ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
)

GEMS_TAXONOMY_CATEGORIES_TABLE = Table(
    "gems_taxonomy_categories",
    metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    Column("parent_category", String(255), nullable=True),
    Column("variables", String(), nullable=True),
    Column("parameters", String(), nullable=True),
    Column("ports", String(), nullable=True),
    Column("extra_outputs", String(), nullable=True),
    Column("properties", String(), nullable=True),
    Column("binding_constraints", String(), nullable=True),
    ForeignKeyConstraint(
        ["study_data_id", "parent_category"],
        ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(["study_data_id"], ["gems_taxonomy_metadata.study_data_id"], ondelete="CASCADE"),
)
