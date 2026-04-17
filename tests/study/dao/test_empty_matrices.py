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
from polars.testing import assert_frame_equal

from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import default_scenario_hourly
from tests.study.dao.conftest import build_real_case_study


def test_empty_matrices(db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]) -> None:
    """
    Test that the DAO methods return the default matrices provided by the simulator if the matrix_id saved in the database corresponds to the null matrix.
    """
    dao, matrix_service = db_dao_930_and_matrix_service
    result = build_real_case_study(dao, matrix_service, null_matrices=True)
    
    area_id, area2 = result.area1, result.area2
    thermal_id, renewable_id, st_storage_id = result.thermal_id, result.renewable_id, result.sts_id
    constraint_id = result.sts_constraint_id
    bc_both_id, bc_eq_id = result.bc_both_id, result.bc_eq_id

    """
    default_matrices = {
        default_cost_level: "sts_cost_level",
        default_energy: "hydro energy",
        default_water_values: "hydro water values",
        default_credit_modulation: "hydro credit modulations",
        default_reservoir: "hydro reservoir",
        default_maxpower: "hydro maxpower",
        default_data: "thermal data",
        default_8_fixed_hourly: ["misc gen", "links parameters before v8.2"],
        default_6_fixed_hourly: "link parameters after v8.2",
        default_4_fixed_hourly: "area reserves",
        default_scenario_monthly: "hydro mod before v6.5",
        default_scenario_hourly_ones: ["sts pmax injection", "sts pmax withdrawal", "sts upper rule curve"],
        default_scenario_daily: ["hydro mod after v6.5", "hydro inflow pattern", "hydro max daily p",
                                 "hydro max daily g"],
        default_scenario_hourly: "the rest",
    }
    """

    default_scenario_hourly_dataframe = create_polars_dataframe(default_scenario_hourly())

    load = dao.get_load(area_id)
    assert_frame_equal(load, default_scenario_hourly_dataframe, check_dtypes=False)

    """
    solar = dao.get_solar(area_id)
    assert_frame_equal(solar, solar_df, check_dtypes=False)

    wind = dao.get_wind(area_id)
    assert_frame_equal(wind, wind_df, check_dtypes=False)

    misc_gen = dao.get_misc_gen(area_id)
    assert_frame_equal(misc_gen, misc_gen_df, check_dtypes=False)

    reserves = dao.get_reserves(area_id)
    assert_frame_equal(reserves, reserves_df, check_dtypes=False)

    link_series = dao.get_link_series(area_id, area2)
    assert_frame_equal(link_series, link_series_df, check_dtypes=False)

    link_direct_capacity = dao.get_link_direct_capacities(area_id, area2)
    assert_frame_equal(link_direct_capacity, link_direct_df, check_dtypes=False)

    link_indirect_capacity = dao.get_link_indirect_capacities(area_id, area2)
    assert_frame_equal(link_indirect_capacity, link_indirect_df, check_dtypes=False)

    thermal_prepro = dao.get_thermal_prepro(area_id, thermal_id)
    assert_frame_equal(thermal_prepro, thermal_prepro_df, check_dtypes=False)

    thermal_modulation = dao.get_thermal_modulation(area_id, thermal_id)
    assert_frame_equal(thermal_modulation, thermal_modulation_df, check_dtypes=False)

    thermal_series = dao.get_thermal_series(area_id, thermal_id)
    assert_frame_equal(thermal_series, thermal_series_df, check_dtypes=False)

    thermal_fuel_cost = dao.get_thermal_fuel_cost(area_id, thermal_id)
    assert_frame_equal(thermal_fuel_cost, thermal_fuel_cost_df, check_dtypes=False)

    thermal_co2_cost = dao.get_thermal_co2_cost(area_id, thermal_id)
    assert_frame_equal(thermal_co2_cost, thermal_co2_cost_df, check_dtypes=False)

    renewable_series = dao.get_renewable_series(area_id, renewable_id)
    assert_frame_equal(renewable_series, renewable_series_df, check_dtypes=False)

    sts_pmax_injection = dao.get_st_storage_pmax_injection(area_id, st_storage_id)
    assert_frame_equal(sts_pmax_injection, sts_pmax_injection_df, check_dtypes=False)

    sts_pmax_withdrawal = dao.get_st_storage_pmax_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_pmax_withdrawal, sts_pmax_withdrawal_df, check_dtypes=False)

    sts_lower_rule_curve = dao.get_st_storage_lower_rule_curve(area_id, st_storage_id)
    assert_frame_equal(sts_lower_rule_curve, sts_lower_rule_curve_df, check_dtypes=False)

    sts_upper_rule_curve = dao.get_st_storage_upper_rule_curve(area_id, st_storage_id)
    assert_frame_equal(sts_upper_rule_curve, sts_upper_rule_curve_df, check_dtypes=False)

    sts_inflows = dao.get_st_storage_inflows(area_id, st_storage_id)
    assert_frame_equal(sts_inflows, sts_inflows_df, check_dtypes=False)

    sts_cost_injection = dao.get_st_storage_cost_injection(area_id, st_storage_id)
    assert_frame_equal(sts_cost_injection, sts_cost_injection_df, check_dtypes=False)

    sts_cost_withdrawal = dao.get_st_storage_cost_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_cost_withdrawal, sts_cost_withdrawal_df, check_dtypes=False)

    sts_cost_level = dao.get_st_storage_cost_level(area_id, st_storage_id)
    assert_frame_equal(sts_cost_level, sts_cost_level_df, check_dtypes=False)

    sts_cost_variation_injection = dao.get_st_storage_cost_variation_injection(area_id, st_storage_id)
    assert_frame_equal(sts_cost_variation_injection, sts_cost_variation_injection_df, check_dtypes=False)

    sts_cost_variation_withdrawal = dao.get_st_storage_cost_variation_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_cost_variation_withdrawal, sts_cost_variation_withdrawal_df, check_dtypes=False)

    sts_constraint_matrix = dao.get_st_storage_additional_constraint_matrix(area_id, st_storage_id, constraint_id)
    assert_frame_equal(sts_constraint_matrix, sts_constraint_matrix_df, check_dtypes=False)

    hydro_maxpower = dao.get_hydro_maxpower(area_id)
    assert_frame_equal(hydro_maxpower, hydro_maxpower_df, check_dtypes=False)

    hydro_reservoir = dao.get_hydro_reservoir(area_id)
    assert_frame_equal(hydro_reservoir, hydro_reservoir_df, check_dtypes=False)

    hydro_energy = dao.get_hydro_energy(area_id)
    assert_frame_equal(hydro_energy, hydro_energy_df, check_dtypes=False)

    hydro_run_of_river = dao.get_hydro_run_of_river(area_id)
    assert_frame_equal(hydro_run_of_river, hydro_run_of_river_df, check_dtypes=False)

    hydro_modulation = dao.get_hydro_modulation(area_id)
    assert_frame_equal(hydro_modulation, hydro_modulation_df, check_dtypes=False)

    hydro_credit_modulations = dao.get_hydro_credit_modulations(area_id)
    assert_frame_equal(hydro_credit_modulations, hydro_credit_modulations_df, check_dtypes=False)

    hydro_inflow_pattern = dao.get_hydro_inflow_pattern(area_id)
    assert_frame_equal(hydro_inflow_pattern, hydro_inflow_pattern_df, check_dtypes=False)

    hydro_water_values = dao.get_hydro_water_values(area_id)
    assert_frame_equal(hydro_water_values, hydro_water_values_df, check_dtypes=False)

    hydro_mingen = dao.get_hydro_mingen(area_id)
    assert_frame_equal(hydro_mingen, hydro_mingen_df, check_dtypes=False)

    hydro_max_hourly_gen_power = dao.get_hydro_max_hourly_gen_power(area_id)
    assert_frame_equal(hydro_max_hourly_gen_power, hydro_max_hourly_gen_power_df, check_dtypes=False)

    hydro_max_hourly_pump_power = dao.get_hydro_max_hourly_pump_power(area_id)
    assert_frame_equal(hydro_max_hourly_pump_power, hydro_max_hourly_pump_power_df, check_dtypes=False)

    hydro_max_daily_gen_energy = dao.get_hydro_max_daily_gen_energy(area_id)
    assert_frame_equal(hydro_max_daily_gen_energy, hydro_max_daily_gen_energy_df, check_dtypes=False)

    hydro_max_daily_pump_energy = dao.get_hydro_max_daily_pump_energy(area_id)
    assert_frame_equal(hydro_max_daily_pump_energy, hydro_max_daily_pump_energy_df, check_dtypes=False)

    xpansion_capacity = dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
    assert_frame_equal(xpansion_capacity, xpansion_capacity_df, check_dtypes=False)

    xpansion_weight = dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
    assert_frame_equal(xpansion_weight, xpansion_weight_df, check_dtypes=False)

    bc_lt = dao.get_constraint_less_term_matrix(bc_both_id)
    assert_frame_equal(bc_lt, bc_lt_df, check_dtypes=False)

    bc_gt = dao.get_constraint_greater_term_matrix(bc_both_id)
    assert_frame_equal(bc_gt, bc_gt_df, check_dtypes=False)

    bc_eq = dao.get_constraint_equal_term_matrix(bc_eq_id)
    assert_frame_equal(bc_eq, bc_eq_df, check_dtypes=False)
    """