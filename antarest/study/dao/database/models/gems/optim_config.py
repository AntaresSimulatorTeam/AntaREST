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
from antarest.study.business.model.gems.optim_config import GemsDecompositionLocation, GemsOutOfBoundsMode
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
    ForeignKeyConstraint(
        ["study_data_id"],
        ["gems_optim_config.study_data_id"],
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
    ForeignKeyConstraint(
        ["study_data_id"],
        ["gems_optim_config.study_data_id"],
        ondelete="CASCADE",
    ),
)


def _create_table(table_name: str, column_name: str, reference_table_name: str) -> Table:
    return Table(
        table_name,
        metadata,
        study_data_id_col(),
        Column("library_id", String(length=255), primary_key=True),
        Column("model_id", String(length=255), primary_key=True),
        Column(column_name, String(length=255), primary_key=True),
        Column("location", enum_col(GemsDecompositionLocation, name="gemsdecompositionlocation"), nullable=False),
        ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", column_name],
            [
                f"{reference_table_name}.study_data_id",
                f"{reference_table_name}.library_id",
                f"{reference_table_name}.model_id",
                f"{reference_table_name}.id",
            ],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id"],
            ["gems_optim_config.study_data_id"],
            ondelete="CASCADE",
        ),
    )


GEMS_OPTIM_CONFIG_MD_VARIABLES_TABLE = _create_table(
    table_name="gems_optim_config_md_variables",
    column_name="variable_id",
    reference_table_name="gems_models_variables",
)

GEMS_OPTIM_CONFIG_MD_CONSTRAINTS_TABLE = _create_table(
    table_name="gems_optim_config_md_constraints",
    column_name="constraint_id",
    reference_table_name="gems_models_constraints",
)

GEMS_OPTIM_CONFIG_MD_OBJECTIVE_CONTRIBUTIONS_TABLE = _create_table(
    table_name="gems_optim_config_md_objective_contributions",
    column_name="objective_contribution_id",
    reference_table_name="gems_models_objective_contributions",
)
