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
from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, Integer, LargeBinary, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.xpansion_model import Master, Solver, UcType
from antarest.study.dao.database.sql_utils import enum_col

metadata = Base.metadata

XPANSION_SETTINGS_TABLE = Table(
    "xpansion_settings",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    # --- XpansionSettings scalars ---
    Column("master", enum_col(Master, name="xpansion_master"), nullable=False),
    Column("uc_type", enum_col(UcType, name="xpansion_uc_type"), nullable=False),
    Column("optimality_gap", Float(), nullable=False),
    Column("relative_gap", Float(), nullable=False),
    Column("relaxed_optimality_gap", Float(), nullable=False),
    Column("max_iteration", Integer(), nullable=False),
    Column("solver", enum_col(Solver, name="xpansion_solver"), nullable=False),
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
    ForeignKeyConstraint(
        ["study_id"],
        ["study_data_container.study_data_id"],
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
    ForeignKeyConstraint(
        ["study_id", "link_area_from", "link_area_to"],
        ["link.study_id", "link.area1", "link.area2"],
        name="fk_xpansion_candidate_link",
        ondelete="CASCADE",
    ),
)

XPANSION_SENSITIVITY_PROJECTION_TABLE = Table(
    "xpansion_sensitivity_projection",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("candidate_name", String(255), nullable=False, primary_key=True),
    ForeignKeyConstraint(
        ["study_id", "candidate_name"],
        ["xpansion_candidate.study_id", "xpansion_candidate.name"],
        name="fk_xpansion_sensitivity_projection_candidate",
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
)

XPANSION_ADEQUACY_CRITERION_TABLE = Table(
    "xpansion_adequacy_criterion",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("stopping_threshold", Float(), nullable=False),
    Column("criterion_count_threshold", Float(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_adequacy_criterion_settings",
        ondelete="CASCADE",
    ),
)

XPANSION_ADEQUACY_PATTERN_TABLE = Table(
    "xpansion_adequacy_pattern",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("area", String(255), nullable=False, primary_key=True),
    Column("criterion", Float(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_adequacy_criterion.study_id"],
        name="fk_xpansion_adequacy_pattern_criterion",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_id", "area"],
        ["area.study_id", "area.area_id"],
        name="fk_xpansion_adequacy_pattern_study_id_area_area",
        ondelete="CASCADE",
    ),
)

XPANSION_CONSTRAINT_TABLE = Table(
    "xpansion_constraint",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("filename", String(255), nullable=False, primary_key=True),
    Column("content", LargeBinary(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_constraint_settings",
        ondelete="CASCADE",
    ),
)

XPANSION_CAPACITY_TABLE = Table(
    "xpansion_capacity",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("filename", String(255), nullable=False, primary_key=True),
    Column("matrix_id", String(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_capacity_settings",
        ondelete="CASCADE",
    ),
)

XPANSION_WEIGHT_TABLE = Table(
    "xpansion_weight",
    metadata,
    Column("study_id", String(36), nullable=False, primary_key=True),
    Column("filename", String(255), nullable=False, primary_key=True),
    Column("matrix_id", String(), nullable=False),
    ForeignKeyConstraint(
        ["study_id"],
        ["xpansion_settings.study_id"],
        name="fk_xpansion_weight_settings",
        ondelete="CASCADE",
    ),
)
