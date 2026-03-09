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
SQLAlchemy Core table definitions for Xpansion storage.

Design decisions:
  - xpansion_settings                    : flat row per study; sensitivity scalars are inlined.
  - xpansion_candidate                   : one row per candidate (individual CRUD, 13 typed fields).
  - xpansion_sensitivity_projection      : one row per projection entry. PK = (study_id, candidate_name).
                                           FK CASCADE to xpansion_candidate: projection rows are removed
                                           when a candidate is deleted. App-level checks
                                           (checks_xpansion_candidate_can_be_deleted) prevent deletion
                                           of candidates still referenced in projection.
  - xpansion_adequacy_criterion          : flat row per study; scalars only (no patterns).
  - xpansion_adequacy_pattern            : one row per XpansionAdequacyPattern. PK = (study_id, area).

Cascade chain:
  study → xpansion_settings → xpansion_candidate → xpansion_sensitivity_projection (CASCADE)
                             → xpansion_adequacy_criterion → xpansion_adequacy_pattern
  Deleting xpansion_settings (i.e. the xpansion configuration) therefore cascades
  to candidates, and transitively to projection entries, the adequacy criterion, and all its patterns.
"""

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.xpansion_model import Master, Solver, UcType

metadata = Base.metadata

_MASTER_ENUM = Enum(Master, name="xpansion_master")
_UC_TYPE_ENUM = Enum(UcType, name="xpansion_uc_type")
_SOLVER_ENUM = Enum(Solver, name="xpansion_solver")

# ---------------------------------------------------------------------------
# xpansion_settings  (1-to-1 with study)
#
# Holds all XpansionSettings scalars plus the inlined XpansionSensitivitySettings.
# sensitivity_projection is a JSON Text column: ["cand_a", "cand_b"]
# ---------------------------------------------------------------------------

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
    ForeignKeyConstraint(
        ["study_id"],
        ["study.id"],
        name="fk_xpansion_settings_study_id",
        ondelete="CASCADE",
    ),
)

# ---------------------------------------------------------------------------
# xpansion_candidate  (1-to-many with xpansion_settings)
#
# One row per XpansionCandidate. PK = (study_id, name).
# FK → xpansion_settings so that deleting the xpansion configuration
# (i.e. the settings row) cascades to all candidates automatically.
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# xpansion_sensitivity_projection  (1-to-many with xpansion_candidate)
#
# One row per entry in XpansionSensitivitySettings.projection. PK = (study_id, candidate_name).
# FK → xpansion_settings (CASCADE): projection rows are removed when the configuration is deleted.
# FK → xpansion_candidate (RESTRICT): the DB prevents deleting a candidate that is still referenced
# in the projection, replacing the equivalent application-level pre-check.
# ---------------------------------------------------------------------------

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
    ),
)

# ---------------------------------------------------------------------------
# xpansion_adequacy_criterion  (1-to-1 with xpansion_settings)
#
# Holds XpansionAdequacyCriterion scalars only.
# Patterns live in xpansion_adequacy_pattern (one row each).
# FK → xpansion_settings so that deleting the xpansion configuration cascades here.
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# xpansion_adequacy_pattern  (1-to-many with xpansion_adequacy_criterion)
#
# One row per XpansionAdequacyPattern. PK = (study_id, area).
# FK → xpansion_adequacy_criterion so that deleting the criterion cascades here.
# ---------------------------------------------------------------------------

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
