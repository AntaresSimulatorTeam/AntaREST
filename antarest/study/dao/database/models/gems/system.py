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
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKeyConstraint, Index, String, Table, Text, text

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


GEMS_COMPONENTS_TABLE = Table(
    "gems_components",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("library_id", String(255), nullable=False),
    Column("model_id", String(255)),
    Column("scenario_group", String(255), nullable=True),
    ForeignKeyConstraint(
        ["study_data_id"],
        ["gems_system_metadata.study_data_id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "model_id", "library_id"],
        ["gems_models.study_data_id", "gems_models.id", "gems_models.library_id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "scenario_group"],
        ["gems_scenario_builder.study_data_id", "gems_scenario_builder.scenario_group"],
        ondelete="SET NULL",
    ),
)

GEMS_COMPONENT_PARAMETERS_TABLE = Table(
    "gems_component_parameters",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("parameter_id", String(255), primary_key=True),
    Column("time_dependent", Boolean, nullable=False),
    Column("scenario_dependent", Boolean, nullable=False),
    # Either a fixed numeric value (e.g. "3.14") or the `id` of a data series (e.g. "demand_profile")
    Column("value", String(255), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_components.study_data_id", "gems_components.component_id"],
        ondelete="CASCADE",
    ),
)

GEMS_COMPONENTS_DATASERIES_TABLE = Table(
    "gems_components_dataseries",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("dataseries_id", String(255), primary_key=True),
    Column("values", Text, nullable=False),
)

GEMS_COMPONENT_PROPERTIES_TABLE = Table(
    "gems_component_properties",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("property_id", String(255), primary_key=True),
    Column("value", String(255), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_components.study_data_id", "gems_components.component_id"],
        ondelete="CASCADE",
    ),
)

GEMS_COMPONENT_CONNECTIONS_TABLE = Table(
    "gems_component_connections",
    metadata,
    study_data_id_col(),
    Column("component1", String(255), primary_key=True),
    Column("component2", String(255), primary_key=True),
    Column("port1", String(255), primary_key=True),
    Column("port2", String(255), primary_key=True),
    # Ensures component1 exists in the study.
    ForeignKeyConstraint(
        ["study_data_id", "component1"],
        [
            "gems_components.study_data_id",
            "gems_components.component_id",
        ],
        name="fk_gems_component_connections_component1_exists",
        ondelete="CASCADE",
    ),
    # Ensures component2 exists in the study.
    ForeignKeyConstraint(
        ["study_data_id", "component2"],
        [
            "gems_components.study_data_id",
            "gems_components.component_id",
        ],
        name="fk_gems_component_connections_component2_exists",
        ondelete="CASCADE",
    ),
    CheckConstraint(
        "component1 != component2 or port1 != port2",
        name="ck_gems_component_connections_have_distinct_endpoints",
    ),
    # A connection between (component1, port1) and (component2, port2) is the same, physically,
    # as its symmetric counterpart. Indexing on the ordered pair forbids declaring both.
    Index(
        "uq_no_inverted_pairs",
        text("(CASE WHEN component1 <= component2 THEN component1 ELSE component2 END)"),
        text("(CASE WHEN component1 >= component2 THEN component1 ELSE component2 END)"),
        text("(CASE WHEN port1 <= port2 THEN port1 ELSE port2 END)"),
        text("(CASE WHEN port1 >= port2 THEN port1 ELSE port2 END)"),
        unique=True,
    ),
)
