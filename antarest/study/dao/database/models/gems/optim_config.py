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
from sqlalchemy import Column, ForeignKeyConstraint, String, Table

from antarest.core.utils.sql_utils import enum_col
from antarest.dbmodel import Base
from antarest.study.business.model.gems.optim_config import GemsOutOfBoundsMode
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

GEMS_OPTIM_CONFIG_OOB_PROCESSING_TABLE = Table(
    "gems_optim_config_oob_processing",
    metadata,
    study_data_id_col(),
    Column("library_id", String(length=255), primary_key=True),
    Column("model_id", String(length=255), primary_key=True),
    Column("constraint_id", String(length=255), primary_key=True),
    Column("mode", enum_col(GemsOutOfBoundsMode, name="gemsoutofboundsmode"), nullable=False),
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
)

GEMS_OPTIM_CONFIG_HEURISTICS_TABLE = Table(
    "gems_optim_config_heuristics",
    metadata,
    study_data_id_col(),
    Column("library_id", String(length=255), primary_key=True),
    Column("model_id", String(length=255), primary_key=True),
    Column("data", String(), nullable=False),  # Data dumped as a JSON
    ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id"],
        ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
        ondelete="CASCADE",
    ),
)

GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_VARIABLES_TABLE = Table(
    "gems_optim_config_model_decomposition_variables",
    metadata,
    study_data_id_col(),
    Column("library_id", String(length=255), primary_key=True),
    Column("model_id", String(length=255), primary_key=True),
    Column("variable_id", String(length=255), primary_key=True),
    Column("location", String(), nullable=False),
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
)

GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_CONSTRAINTS_TABLE = Table(
    "gems_optim_config_model_decomposition_constraints",
    metadata,
    study_data_id_col(),
    Column("library_id", String(length=255), primary_key=True),
    Column("model_id", String(length=255), primary_key=True),
    Column("constraint_id", String(length=255), primary_key=True),
    Column("location", String(), nullable=False),
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
)

GEMS_OPTIM_CONFIG_MODEL_DECOMPOSITION_OBJECTIVE_CONTRIBUTIONS_TABLE = Table(
    "gems_optim_config_model_decomposition_objective_contributions",
    metadata,
    study_data_id_col(),
    Column("library_id", String(length=255), primary_key=True),
    Column("model_id", String(length=255), primary_key=True),
    Column("objective_contribution_id", String(length=255), primary_key=True),
    Column("location", String(), nullable=False),
    ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id", "objective_contribution_id"],
        [
            "gems_models_objective_contributions.study_data_id",
            "gems_models_objective_contributions.library_id",
            "gems_models_objective_contributions.model_id",
            "gems_models_objective_contributions.id",
        ],
        name="fk_gems_optim_config_model_decomposition_objective_contribution",
        ondelete="CASCADE",
    ),
)
