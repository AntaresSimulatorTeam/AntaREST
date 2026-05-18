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
SQLAlchemy Core table definitions for binding constraint storage.

This module defines the database tables used for storing binding constraint data
when a study has storage_mode=DATABASE.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.binding_constraint_model import BindingConstraintFrequency, BindingConstraintOperator
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

BINDING_CONSTRAINT_TABLE = Table(
    "binding_constraint",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("time_step", enum_col(BindingConstraintFrequency, name="bc_frequency"), nullable=False),
    Column("operator", enum_col(BindingConstraintOperator, name="bc_operator"), nullable=False),
    Column("comments", String, nullable=False),
    # Nullable: only present for study versions >= 8.3
    Column("filter_year_by_year", String, nullable=True),
    Column("filter_synthesis", String, nullable=True),
    # Nullable: only present for study versions >= 8.7
    Column("group", String(255), nullable=True),
    ForeignKeyConstraint(
        ["study_id"],
        ["study.id"],
        name="fk_binding_constraint_study_id",
        ondelete="CASCADE",
    ),
)

BINDING_CONSTRAINT_LINK_TERM_TABLE = Table(
    "binding_constraint_link_term",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("area1", String(255), nullable=False, primary_key=True),
    Column("area2", String(255), nullable=False, primary_key=True),
    Column("weight", Float, nullable=False),
    Column("offset", Integer, nullable=True),
    ForeignKeyConstraint(
        ["study_id", "constraint_id"],
        ["binding_constraint.study_id", "binding_constraint.constraint_id"],
        name="fk_bc_link_term_constraint",
        ondelete="CASCADE",
    ),
)

BINDING_CONSTRAINT_CLUSTER_TERM_TABLE = Table(
    "binding_constraint_cluster_term",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("area", String(255), nullable=False, primary_key=True),
    Column("cluster", String(255), nullable=False, primary_key=True),
    Column("weight", Float, nullable=False),
    Column("offset", Integer, nullable=True),
    ForeignKeyConstraint(
        ["study_id", "constraint_id"],
        ["binding_constraint.study_id", "binding_constraint.constraint_id"],
        name="fk_bc_cluster_term_constraint",
        ondelete="CASCADE",
    ),
)


def _create_bc_matrix_table(name: str) -> Table:
    return Table(
        name,
        metadata,
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("constraint_id", String(255), nullable=False, primary_key=True),
        Column("matrix_id", String(64), nullable=False),
        ForeignKeyConstraint(
            ["study_id", "constraint_id"],
            ["binding_constraint.study_id", "binding_constraint.constraint_id"],
            name=f"fk_{name}_constraint",
            ondelete="CASCADE",
        ),
    )


# Pre-v8.7: single 2nd-member matrix
BINDING_CONSTRAINT_VALUES_MATRIX_TABLE = _create_bc_matrix_table("binding_constraint_values_matrix")
# v8.7+: per-operator term matrices
BINDING_CONSTRAINT_LT_MATRIX_TABLE = _create_bc_matrix_table("binding_constraint_lt_matrix")
BINDING_CONSTRAINT_GT_MATRIX_TABLE = _create_bc_matrix_table("binding_constraint_gt_matrix")
BINDING_CONSTRAINT_EQ_MATRIX_TABLE = _create_bc_matrix_table("binding_constraint_eq_matrix")
