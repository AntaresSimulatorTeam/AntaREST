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
from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata


GEMS_SYSTEM_METADATA_TABLE = Table(
    "gems_system_metadata",
    metadata,
    study_data_id_col(),
    Column("system_id", String(255), nullable=False),
    Column("description", String(255)),
    ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
)


GEMS_COMPONENT_TABLE = Table(
    "gems_system_component",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("model_id", String(255)),
    Column("scenario_group", String(255), nullable=True),
    ForeignKeyConstraint(
        ["study_data_id"],
        ["gems_system_metadata.study_data_id"],
        ondelete="CASCADE",
    ),
)

GEMS_PARAMETER_TABLE = Table(
    "gems_system_parameter",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("parameter_id", String(255), primary_key=True),
    Column("time_dependent", Boolean, nullable=False),
    Column("scenario_dependent", Boolean, nullable=False),
    Column("value", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_system_component.study_data_id", "gems_system_component.component_id"],
        ondelete="CASCADE",
    ),
)

GEMS_PROPERTIES_TABLE = Table(
    "gems_system_property",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("property_id", String(255), primary_key=True),
    Column("value", String(255), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_system_component.study_data_id", "gems_system_component.component_id"],
        ondelete="CASCADE",
    ),
)
