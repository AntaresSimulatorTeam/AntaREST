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
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.config.general_model import BuildingMode, Mode, Month, WeekDay
from antarest.study.business.model.config.optimization_config_model import (
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)

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

ADVANCED_PARAMETERS_TABLE = Table(
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

COMPATIBILITY_PARAMETERS_TABLE = Table(
    "compatibility_parameters",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("hydro_pmax", Enum(HydroPmax), nullable=True),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_compatibility_parameters_study_id", ondelete="CASCADE"),
)

OPTIMIZATION_PREFERENCES_TABLE = Table(
    "optimization_preferences",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("binding_constraints", Boolean(), nullable=False),
    Column("hurdle_costs", Boolean(), nullable=False),
    Column("transmission_capacities", String(), nullable=False),
    Column("thermal_clusters_min_stable_power", Boolean(), nullable=False),
    Column("thermal_clusters_min_ud_time", Boolean(), nullable=False),
    Column("day_ahead_reserve", Boolean(), nullable=False),
    Column("primary_reserve", Boolean(), nullable=False),
    Column("strategic_reserve", Boolean(), nullable=False),
    Column("spinning_reserve", Boolean(), nullable=False),
    Column("export_mps", String(), nullable=False),
    Column("unfeasible_problem_behavior", Enum(UnfeasibleProblemBehavior), nullable=False),
    Column("simplex_optimization_range", Enum(SimplexOptimizationRange), nullable=False),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_optimization_preferences_study_id", ondelete="CASCADE"),
)

TIMESERIES_CONFIG_TABLE = Table(
    "compatibility_parameters",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("thermal_number", Integer(), nullable=False),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_timeseries_config_study_id", ondelete="CASCADE"),
)

PLAYLIST_TABLE = Table(
    "compatibility_parameters",
    metadata,
    Column("study_id", String(length=36), nullable=False),
    Column("years", String(), nullable=False),
    ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_playlist_study_id", ondelete="CASCADE"),
)
