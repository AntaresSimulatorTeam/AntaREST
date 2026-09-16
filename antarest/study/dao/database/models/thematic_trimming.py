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

from sqlalchemy import JSON, Column, ForeignKeyConstraint, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

# Relation: One to one with `Study`

THEMATIC_TRIMMING_TABLE = Table(
    "thematic_trimming",
    metadata,
    study_data_id_col(),
    Column("thematic_trimming", JSON(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id"],
        ["study_data.study_data_id"],
        name="fk_thematic_trimming_study_data_id_study",
        ondelete="CASCADE",
    ),
)
