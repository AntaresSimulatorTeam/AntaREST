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
from sqlalchemy import Column, ForeignKey, String, Table

from antarest.dbmodel import Base

metadata = Base.metadata

STUDY_DATA_CONTAINER_TABLE = Table(
    "study_data_container",
    metadata,
    Column("study_id", String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False, primary_key=True),
    Column("study_data_id", String(36), nullable=False),
)
