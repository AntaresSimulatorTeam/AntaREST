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
    Column("value", Float, nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_components.study_data_id", "gems_components.component_id"],
        ondelete="CASCADE",
    ),
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


def _component_foreign_key(table_name: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["study_data_id", "component_id"],
        ["gems_components.study_data_id", "gems_components.component_id"],
        name=f"fk_{table_name}_component",
        ondelete="CASCADE",
    )


# There is no foreign key to the port of the component: models and ports are never deleted,
# so it could only check the port on insertion, which is already done application side.
# Antares Simulator allows a single area connection per port, hence the primary key.
GEMS_AREA_CONNECTIONS_TABLE = Table(
    "gems_area_connections",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("port_id", String(255), primary_key=True),
    Column("area_id", String(255), nullable=False),
    _component_foreign_key("gems_area_connections"),
    ForeignKeyConstraint(
        ["study_data_id", "area_id"],
        ["area.study_data_id", "area.area_id"],
        name="fk_gems_area_connections_area",
        ondelete="CASCADE",
    ),
)

# Same design as `gems_area_connections`, with a legacy thermal cluster as target.
GEMS_THERMAL_CAPACITY_CONNECTIONS_TABLE = Table(
    "gems_thermal_capacity_connections",
    metadata,
    study_data_id_col(),
    Column("component_id", String(255), primary_key=True),
    Column("port_id", String(255), primary_key=True),
    Column("area_id", String(255), nullable=False),
    Column("cluster_id", String(255), nullable=False),
    _component_foreign_key("gems_thermal_capacity_connections"),
    ForeignKeyConstraint(
        ["study_data_id", "area_id", "cluster_id"],
        ["thermal_cluster.study_data_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
        name="fk_gems_thermal_capacity_connections_cluster",
        ondelete="CASCADE",
    ),
)
