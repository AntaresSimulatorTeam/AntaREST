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
from sqlalchemy import Boolean, Column, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

GEMS_LIBRARY_METADATA_TABLE = Table(
    "gems_library_metadata",
    metadata,
    study_data_id_col(),
    Column("id", String(255), nullable=False),
    Column("description", String(), nullable=True),
    Column("version", String(36), nullable=True),
    ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
)

GEMS_PORT_TYPES_TABLE = Table(
    "gems_port_types",
    metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    Column("description", String(), nullable=True),
    Column("fields", String(), nullable=False),
    ForeignKeyConstraint(["study_data_id"], ["gems_library_metadata.study_data_id"], ondelete="CASCADE"),
)

GEMS_MODELS_TABLE = Table(
    "gems_models",
    metadata,
    study_data_id_col(),
    Column("id", String(255), primary_key=True),
    Column("description", String(), nullable=True),
    Column("taxonomy_category", String(), nullable=True),
    Column("properties", String(), nullable=True),
    Column("variables", String(), nullable=False),
    Column("binding_constraints", String(), nullable=False),
    Column("constraints", String(), nullable=False),
    Column("objective_contributions", String(), nullable=False),
    Column("extra_outputs", String(), nullable=False),
    Column("port_field_definitions", String(), nullable=False),
    ForeignKeyConstraint(["study_data_id"], ["gems_library_metadata.study_data_id"], ondelete="CASCADE"),
)

GEMS_MODELS_PORTS_TABLE = Table(
    "gems_models_ports",
    metadata,
    study_data_id_col(),
    Column("model_id", String(255), primary_key=True),
    Column("port_id", String(255), primary_key=True),
    Column("type", String(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "model_id"],
        ["gems_models.study_data_id", "gems_models.id"],
        ondelete="CASCADE",
    ),
)

GEMS_MODELS_PARAMETERS_TABLE = Table(
    "gems_models_parameters",
    metadata,
    study_data_id_col(),
    Column("model_id", String(255), primary_key=True),
    Column("parameter_id", String(255), primary_key=True),
    Column("time_dependent", Boolean(), nullable=False),
    Column("scenario_dependent", Boolean(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "model_id"],
        ["gems_models.study_data_id", "gems_models.id"],
        ondelete="CASCADE",
    ),
)
