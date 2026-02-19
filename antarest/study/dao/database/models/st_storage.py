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
SQLAlchemy Core table definitions for short-term storage.
"""

from sqlalchemy import JSON, Boolean, Column, Enum, Float, ForeignKeyConstraint, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.sts_model import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
)

metadata = Base.metadata

_VARIABLE_ENUM = Enum(AdditionalConstraintVariable, name="additionalconstraintvariable")
_OPERATOR_ENUM = Enum(AdditionalConstraintOperator, name="additionalconstraintoperator")


ST_STORAGE_TABLE = Table(
    "st_storage",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("st_storage_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("group", String(255), nullable=False),
    Column("injection_nominal_capacity", Float, nullable=False),
    Column("withdrawal_nominal_capacity", Float, nullable=False),
    Column("reservoir_capacity", Float, nullable=False),
    Column("efficiency", Float, nullable=False),
    Column("initial_level", Float, nullable=False),
    Column("initial_level_optim", Boolean, nullable=False),
    Column("enabled", Boolean, nullable=True),
    Column("efficiency_withdrawal", Float, nullable=True),
    Column("penalize_variation_injection", Boolean, nullable=True),
    Column("penalize_variation_withdrawal", Boolean, nullable=True),
    Column("allow_overflow", Boolean, nullable=True),
    ForeignKeyConstraint(["study_id", "area_id"], ["area.study_id", "area.area_id"], ondelete="CASCADE"),
)


def _create_st_storage_matrix_table(name: str) -> Table:
    return Table(
        name,
        metadata,
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("st_storage_id", String(255), nullable=False, primary_key=True),
        Column("matrix_id", String(64), nullable=False),
        ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id"],
            ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
            ondelete="CASCADE",
        ),
    )


PMAX_INJECTION_TABLE = _create_st_storage_matrix_table("pmax_injection")
PMAX_WITHDRAWAL_TABLE = _create_st_storage_matrix_table("pmax_withdrawal")
LOWER_RULE_CURVE_TABLE = _create_st_storage_matrix_table("lower_rule_curve")
UPPER_RULE_CURVE_TABLE = _create_st_storage_matrix_table("upper_rule_curve")
INFLOWS_TABLE = _create_st_storage_matrix_table("inflows")
COST_INJECTION_TABLE = _create_st_storage_matrix_table("cost_injection")
COST_WITHDRAWAL_TABLE = _create_st_storage_matrix_table("cost_withdrawal")
COST_LEVEL_TABLE = _create_st_storage_matrix_table("cost_level")
COST_VARIATION_INJECTION_TABLE = _create_st_storage_matrix_table("cost_variation_injection")
COST_VARIATION_WITHDRAWAL_TABLE = _create_st_storage_matrix_table("cost_variation_withdrawal")


ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE = Table(
    "st_storage_additional_constraint",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("st_storage_id", String(255), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("variable", _VARIABLE_ENUM, nullable=False),
    Column("operator", _OPERATOR_ENUM, nullable=False),
    Column("occurrences", JSON, nullable=False),
    Column("enabled", Boolean, nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "st_storage_id"],
        ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
        ondelete="CASCADE",
    ),
)

ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE = Table(
    "st_storage_additional_constraint_matrix",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area_id", String(255), nullable=False, primary_key=True),
    Column("st_storage_id", String(255), nullable=False, primary_key=True),
    Column("constraint_id", String(255), nullable=False, primary_key=True),
    Column("matrix_id", String(64), nullable=False),
    ForeignKeyConstraint(
        ["study_id", "area_id", "st_storage_id", "constraint_id"],
        [
            "st_storage_additional_constraint.study_id",
            "st_storage_additional_constraint.area_id",
            "st_storage_additional_constraint.st_storage_id",
            "st_storage_additional_constraint.constraint_id",
        ],
        ondelete="CASCADE",
    ),
)
