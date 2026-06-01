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

from sqlalchemy import JSON, Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

# Relation: One to one with `Study`

THEMATIC_TRIMMING_TABLE = Table(
    "thematic_trimming",
    metadata,
    Column("study_id", String(length=36), nullable=False, primary_key=True),
    Column("thematic_trimming", JSON(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"], ["study_data_container.study_id"], name="fk_thematic_trimming_study_id_study", ondelete="CASCADE"
    ),
)
