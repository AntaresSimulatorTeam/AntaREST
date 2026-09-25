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

GEMS_CATALOGS_TABLE = Table(
    "gems_catalogs",
    Base.metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    Column("taxonomy", String(255), nullable=False),
    Column("location", String(255), nullable=False),
    # Metric definitions are stored as JSON, like the cold sections of GEMS libraries and taxonomies.
    Column("metrics_definition", String(), nullable=False),
    ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
)
