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

from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters, PriceTakingOrder
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters, HydroPmax
from antarest.study.business.model.config.general_model import BuildingMode, GeneralConfig, Mode, Month, WeekDay
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    SimplexOptimizationRange,
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
)
from antarest.study.business.model.config.playlist_model import Playlist, PlaylistValues
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration, TimeSeriesType
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.comments import COMMENTS_TABLE
from antarest.study.model import STUDY_VERSION_9_3
from tests.study.dao.conftest import build_db_dao


def test_nominal_case(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    # General Config
    new_general_config = GeneralConfig(
        mode=Mode.ECONOMY,
        first_day=4,
        last_day=5,
        horizon="2039",
        first_month=Month.APRIL,
        first_week_day=WeekDay.TUESDAY,
        first_january=WeekDay.SUNDAY,
        leap_year=True,
        nb_years=4,
        building_mode=BuildingMode.CUSTOM,
        selection_mode=True,
        year_by_year=True,
        simulation_synthesis=False,
        mc_scenario=True,
        geographic_trimming=True,
        thematic_trimming=False,
    )
    dao.save_general_config(new_general_config)
    assert dao.get_general_config() == new_general_config

    # Advanced Parameters
    new_parameters = AdvancedParameters(
        accuracy_on_correlation="solar",
        power_fluctuations=PowerFluctuation.MINIMIZE_EXCURSIONS,
        shedding_policy=SheddingPolicy.MINIMIZE_DURATION,
        hydro_pricing_mode=HydroPricingMode.ACCURATE,
        hydro_heuristic_policy=HydroHeuristicPolicy.MAXIMIZE_GENERATION,
        unit_commitment_mode=UnitCommitmentMode.MILP,
        number_of_cores_mode=SimulationCore.MAXIMUM,
        renewable_generation_modelling=RenewableGenerationModeling.AGGREGATED,
        seed_tsgen_wind=1,
        seed_tsgen_load=1,
        seed_tsgen_hydro=1,
        seed_tsgen_thermal=1,
        seed_tsgen_solar=1,
        seed_tsnumbers=1,
        seed_unsupplied_energy_costs=1,
        seed_spilled_energy_costs=1,
        seed_thermal_costs=1,
        seed_hydro_costs=1,
        seed_initial_reservoir_levels=1,
        initial_reservoir_levels=InitialReservoirLevel.HOT_START,
    )
    dao.save_advanced_parameters(new_parameters)
    assert dao.get_advanced_parameters() == new_parameters

    # AdequacyPatch Parameters
    params = AdequacyPatchParameters(
        enable_adequacy_patch=True,
        ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch=False,
        price_taking_order=PriceTakingOrder.LOAD,
        include_hurdle_cost_csr=True,
        check_csr_cost_function=True,
        threshold_initiate_curtailment_sharing_rule=4.2,
        threshold_display_local_matching_rule_violations=3.14,
        threshold_csr_variable_bounds_relaxation=144,
        # Appeared in v8.3 and removed in v9.2
        ntc_between_physical_areas_out_adequacy_patch=True,
    )
    dao.save_adequacy_patch_parameters(params)
    assert dao.get_adequacy_patch_parameters() == params

    # TimeSeries Config
    timeseries = TimeSeriesConfiguration(thermal=TimeSeriesType(number=4))
    dao.save_timeseries_config(timeseries)
    assert dao.get_timeseries_config() == timeseries

    # Playlist Config
    playlist = Playlist(years={4: PlaylistValues(status=False, weight=0.2), 7: PlaylistValues(weight=1.1)})
    dao.save_playlist_config(playlist)
    assert dao.get_playlist_config() == playlist

    # Optimization preferences
    preferences = OptimizationPreferences(
        binding_constraints=False,
        hurdle_costs=False,
        transmission_capacities=TransmissionCapacities.INFINITE_FOR_ALL_LINKS,
        thermal_clusters_min_stable_power=False,
        thermal_clusters_min_ud_time=False,
        day_ahead_reserve=False,
        primary_reserve=False,
        strategic_reserve=False,
        spinning_reserve=False,
        export_mps="optim-1",
        unfeasible_problem_behavior=UnfeasibleProblemBehavior.ERROR_DRY,
        simplex_optimization_range=SimplexOptimizationRange.DAY,
    )
    dao.save_optimization_preferences(preferences)
    assert dao.get_optimization_preferences() == preferences


def test_compatibility_parameters(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    # Create a study in version 9.3 to test the compatibility parameters
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    assert dao.get_compatibility_parameters() == CompatibilityParameters()
    new_parameters = CompatibilityParameters(hydro_pmax=HydroPmax.HOURLY)
    dao.save_compatibility_parameters(new_parameters)
    assert dao.get_compatibility_parameters() == new_parameters


def test_get_comments_returns_empty_string_by_default(db_dao: DatabaseStudyDao) -> None:
    assert db_dao.get_comments() == ""


def test_save_comments_persists_value(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao
    comments = "test comment study"

    dao.save_comments(comments)

    assert dao.get_comments() == comments

    stmt = select(COMMENTS_TABLE.c.comments).where(COMMENTS_TABLE.c.study_id == dao.get_study_id())
    assert db_session.execute(stmt).scalar_one() == comments
