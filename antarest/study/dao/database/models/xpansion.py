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
from sqlalchemy import JSON, Boolean, Column, Enum, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.xpansion_model import Master, Solver, UcType

metadata = Base.metadata

_MASTER_ENUM = Enum(Master, name="xpansion_master")
_UC_TYPE_ENUM = Enum(UcType, name="xpansion_uc_type")
_SOLVER_ENUM = Enum(Solver, name="xpansion_solver")

XPANSION_SETTINGS_TABLE = Table(
    "xpansion_settings",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    # --- XpansionSettings scalars ---
    Column("master", _MASTER_ENUM, nullable=False),
    Column("uc_type", _UC_TYPE_ENUM, nullable=False),
    Column("optimality_gap", Float(), nullable=False),
    Column("relative_gap", Float(), nullable=False),
    Column("relaxed_optimality_gap", Float(), nullable=False),
    Column("max_iteration", Integer(), nullable=False),
    Column("solver", _SOLVER_ENUM, nullable=False),
    Column("log_level", Integer(), nullable=False),
    Column("separation_parameter", Float(), nullable=False),
    Column("batch_size", Integer(), nullable=False),
    Column("yearly_weights", String(), nullable=False),
    Column("additional_constraints", String(), nullable=False),
    Column("timelimit", Integer(), nullable=False),
    Column("master_solution_tolerance", Float(), nullable=False),
    Column("cut_coefficient_tolerance", Float(), nullable=False),
    # --- XpansionSensitivitySettings (inlined) ---
    Column("sensitivity_epsilon", Float(), nullable=False),
    Column("sensitivity_capex", Boolean(), nullable=False),
    Column("sensitivity_projection", JSON(), nullable=False),  # JSON: ["cand_a", "cand_b"]
    ForeignKeyConstraint(
        ["study_id"],
        ["study.id"],
        name="fk_xpansion_settings_study_id",
        ondelete="CASCADE",
    ),
)

XPANSION_CANDIDATE_TABLE = Table(
    "xpansion_candidate",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("name", String(255), nullable=False, primary_key=True),
    Column("link_area_from", String(255), nullable=False),
    Column("link_area_to", String(255), nullable=False),
    Column("annual_cost_per_mw", Float(), nullable=False),
    Column("unit_size", Float(), nullable=True),
    Column("max_units", Integer(), nullable=True),
    Column("max_investment", Float(), nullable=True),
    Column("already_installed_capacity", Integer(), nullable=True),
    Column("link_profile", String(255), nullable=True),
    Column("already_installed_link_profile", String(255), nullable=True),
    Column("direct_link_profile", String(255), nullable=True),
    Column("indirect_link_profile", String(255), nullable=True),
    Column("already_installed_direct_link_profile", String(255), nullable=True),
    Column("already_installed_indirect_link_profile", String(255), nullable=True),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_candidate_settings",
        ondelete="CASCADE",
    ),
)

XPANSION_ADEQUACY_CRITERION_TABLE = Table(
    "xpansion_adequacy_criterion",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("stopping_threshold", Float(), nullable=False),
    Column("criterion_count_threshold", Float(), nullable=False),
    Column("patterns", JSON(), nullable=False),  # JSON: [{"area": "x", "criterion": 1.0}]
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_adequacy_criterion_settings",
        ondelete="CASCADE",
    ),
)
