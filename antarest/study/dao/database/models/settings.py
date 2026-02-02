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

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKeyConstraint, Integer, String, Table

from antarest.dbmodel import Base
from antarest.study.business.model.config.adequacy_patch_model import PriceTakingOrder
from antarest.study.business.model.config.general_model import BuildingMode, Mode, Month, WeekDay

metadata = Base.metadata

# Relations: One to one with `Study`

"""
op.drop_table("general_config")
op.drop_table("advanced_parameters")
op.drop_table("adequacy_patch_parameters")
op.drop_table("compatibility_parameters")
op.drop_table("optimization_preferences")
op.drop_table("timeseries_config")
op.drop_table("playlist")
"""

GENERAL_CONFIG_TABLE = Table(
    "general_config",
    metadata,
    Column("study_id", String(length=36), nullable=False, primary_key=True),
    Column("mode", Enum(Mode), nullable=False),
    Column("first_day", Integer(), nullable=False),
    Column("last_day", Integer(), nullable=False),
    Column("horizon", String(), nullable=False),
    Column("first_month", Enum(Month), nullable=False),
    Column("first_week_day", Enum(WeekDay), nullable=False),
    Column("first_january", Enum(WeekDay), nullable=False),
    Column("leap_year", Boolean(), nullable=False),
    Column("nb_years", Integer(), nullable=False),
    Column("building_mode", Enum(BuildingMode), nullable=False),
    Column("selection_mode", Boolean(), nullable=False),
    Column("year_by_year", Boolean(), nullable=False),
    Column("simulation_synthesis", Boolean(), nullable=False),
    Column("mc_scenario", Boolean(), nullable=False),
    Column("filtering", Boolean(), nullable=True),
    Column("geographic_trimming", Boolean(), nullable=True),
    Column("thematic_trimming", Boolean(), nullable=True),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_general_config_study_id", ondelete="CASCADE"),
)

ADVANCED_PARAMETERS = Table(
    "advanced_parameters",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("enable_adequacy_patch", Boolean(), nullable=False),
    Column("ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch", Boolean(), nullable=False),
    Column("price_taking_order", Enum(PriceTakingOrder), nullable=True),
    Column("include_hurdle_cost_csr", Boolean(), nullable=True),
    Column("check_csr_cost_function", Boolean(), nullable=True),
    Column("threshold_initiate_curtailment_sharing_rule", Float(), nullable=True),
    Column("threshold_display_local_matching_rule_violations", Float(), nullable=True),
    Column("threshold_csr_variable_bounds_relaxation", Integer(), nullable=True),
    Column("ntc_between_physical_areas_out_adequacy_patch", Boolean(), nullable=True),
    Column("redispatch", Boolean(), nullable=True),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_adequacy_patch_parameters_study_id", ondelete="CASCADE"),
)
