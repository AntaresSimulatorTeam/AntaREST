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

"""
SQLAlchemy Core table definitions for rulesets.
"""
from sqlalchemy import Table, Column, String, ForeignKeyConstraint, Enum, JSON

from antarest.dbmodel import Base
from antarest.study.business.model.scenario_builder_model import ScenarioType

metadata = Base.metadata

_SCENARIO_TYPE_ENUM = Enum(ScenarioType, name="scenariotype")

RULESET_TABLE = Table(
    "ruleset",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
)

RULESET_AREA_TABLE = Table(
    "ruleset_area",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("scenario_type", _SCENARIO_TYPE_ENUM, nullable=False, primary_key=True),
    Column("timeseries", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "ruleset_name"], ["ruleset.study_id", "ruleset.ruleset_name"], name="fk_ruleset_area", ondelete="CASCADE"
    )
)

RULESET_LINK_TABLE = Table(
    "ruleset_link",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    Column("link_id", String(255), nullable=False, primary_key=True),
    Column("timeseries", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "ruleset_name"], ["ruleset.study_id", "ruleset.ruleset_name"], name="fk_ruleset_link",
        ondelete="CASCADE"
    )
)

RULESET_BC_GROUP_TABLE = Table(
    "ruleset_bc_group",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    Column("bc_group_id", String(255), nullable=False, primary_key=True),
    Column("timeseries", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "ruleset_name"], ["ruleset.study_id", "ruleset.ruleset_name"], name="fk_ruleset_bc_group",
        ondelete="CASCADE"
    )
)

RULESET_AREA_ITEM_TABLE = Table(
    "ruleset_area_item",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("item_id", String(255), nullable=False, primary_key=True),
    Column("scenario_type", _SCENARIO_TYPE_ENUM, nullable=False, primary_key=True),
    Column("timeseries", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "ruleset_name"], ["ruleset.study_id", "ruleset.ruleset_name"], name="fk_ruleset_area_item", ondelete="CASCADE"
    )
)

RULESET_AREA_ITEM_CONSTRAINT_TABLE = Table(
    "ruleset_area_item_constraint",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("ruleset_name", String(255), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("item_id", String(255), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("timeseries", JSON, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "ruleset_name"], ["ruleset.study_id", "ruleset.ruleset_name"], name="fk_ruleset_area_item_constraint", ondelete="CASCADE"
    )
)