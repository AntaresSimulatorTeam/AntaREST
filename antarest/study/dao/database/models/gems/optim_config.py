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
from sqlalchemy import Column, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.dao.database.models import study_data_id_col

metadata = Base.metadata

GEMS_OPTIM_CONFIG_TABLE = Table(
    "gems_optim_config",
    metadata,
    study_data_id_col(),
    Column("time_scope", String(), nullable=True),
    Column("scenario_scope", String(), nullable=True),
    Column("solver_options", String(), nullable=True),
    Column("resolution", String(), nullable=True),
    ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
)

# Each model entry of the configuration is stored as:
#   - one row without any element id, holding the model itself (and its heuristics)
#   - one row per variable, constraint or objective contribution the entry refers to
GEMS_OPTIM_CONFIG_MODELS_TABLE = Table(
    "gems_optim_config_models",
    metadata,
    Column("id", Integer(), primary_key=True, autoincrement=True),
    study_data_id_col(primary_key=False),
    Column("library_id", String(255), nullable=False),
    Column("model_id", String(255), nullable=False),
    Column("variable_id", String(255), nullable=True),
    Column("constraint_id", String(255), nullable=True),
    Column("objective_contribution_id", String(255), nullable=True),
    # out-of-bounds-processing mode (constraints only)
    Column("out_of_bounds_mode", String(255), nullable=True),
    # model-decomposition location
    Column("location", String(255), nullable=True),
    # heuristics, stored as JSON on the model row
    Column("heuristics", String(), nullable=True),
    ForeignKeyConstraint(["study_data_id"], ["gems_optim_config.study_data_id"], ondelete="CASCADE"),
    ForeignKeyConstraint(
        ["study_data_id", "model_id", "library_id"],
        ["gems_models.study_data_id", "gems_models.id", "gems_models.library_id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id", "variable_id"],
        [
            "gems_models_variables.study_data_id",
            "gems_models_variables.library_id",
            "gems_models_variables.model_id",
            "gems_models_variables.id",
        ],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id", "constraint_id"],
        [
            "gems_models_constraints.study_data_id",
            "gems_models_constraints.library_id",
            "gems_models_constraints.model_id",
            "gems_models_constraints.id",
        ],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id", "objective_contribution_id"],
        [
            "gems_models_objective_contributions.study_data_id",
            "gems_models_objective_contributions.library_id",
            "gems_models_objective_contributions.model_id",
            "gems_models_objective_contributions.id",
        ],
        ondelete="CASCADE",
    ),
)
