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

from sqlalchemy import Column, Float, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

# An area owns exactly one long-term storage, so there is no asset column here: a row is
# identified by the area and the reserve alone. Deleting an area cascades through
# `reserve_definition`, which is why a single foreign key is enough.
HYDRO_RESERVE_CERTIFICATION_TABLE = Table(
    "hydro_reserve_certifications",
    metadata,
    study_data_id_col(),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("reserve_id", String(255), nullable=False, primary_key=True),
    Column("participation_cost", Float, nullable=False),
    Column("max_release", Float, nullable=False),
    Column("max_store", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "area_id", "reserve_id"],
        ["reserve_definition.study_data_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
        ondelete="CASCADE",
    ),
)
