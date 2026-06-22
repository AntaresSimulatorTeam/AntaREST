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
import polars as pl
from polars.testing import assert_frame_equal

from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import (
    default_4_fixed_hourly,
    default_6_fixed_hourly,
    default_8_fixed_hourly,
    default_cost_level,
    default_credit_modulation,
    default_energy,
    default_maxpower,
    default_reservoir,
    default_scenario_daily,
    default_scenario_hourly,
    default_scenario_hourly_ones,
    default_water_values,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    default_data_matrix,
    default_modulation_matrix,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly,
    default_bc_weekly_daily,
)
from tests.study.dao.conftest import build_real_case_study, build_reserve_definition
from tests.study.dao.utils import save_area


def test_empty_matrices(dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService]) -> None:
    """
    Parametrized test for both FS and DB DAOs.
    Ensures DAO methods return the default matrices when the null_matrix is saved.
    """
    dao, matrix_service = dao_and_matrix_service
    result = build_real_case_study(dao, matrix_service, null_matrices=True)

    area_id, area2 = result.area1, result.area2
    thermal_id, renewable_id, st_storage_id = result.thermal_id, result.renewable_id, result.sts_id
    constraint_id = result.sts_constraint_id
    bc_both_id, bc_eq_id = result.bc_both_id, result.bc_eq_id

    # Declare expected dataframes
    default_scenario_hourly_dataframe = create_polars_dataframe(default_scenario_hourly())
    default_8_fixed_hourly_dataframe = create_polars_dataframe(default_8_fixed_hourly())
    default_6_fixed_hourly_dataframe = create_polars_dataframe(default_6_fixed_hourly())
    default_4_fixed_hourly_dataframe = create_polars_dataframe(default_4_fixed_hourly())
    default_data_dataframe = create_polars_dataframe(default_data_matrix())
    default_modulation_dataframe = create_polars_dataframe(default_modulation_matrix())
    default_scenario_hourly_ones_dataframe = create_polars_dataframe(default_scenario_hourly_ones())
    default_cost_level_dataframe = create_polars_dataframe(default_cost_level())
    default_maxpower_dataframe = create_polars_dataframe(default_maxpower())
    default_reservoir_dataframe = create_polars_dataframe(default_reservoir())
    default_energy_dataframe = create_polars_dataframe(default_energy())
    default_scenario_daily_dataframe = create_polars_dataframe(default_scenario_daily())
    default_water_values_dataframe = create_polars_dataframe(default_water_values())
    default_credit_modulation_dataframe = create_polars_dataframe(default_credit_modulation())
    default_bc_hourly_dataframe = create_polars_dataframe(default_bc_hourly())
    default_bc_daily_weekly_dataframe = create_polars_dataframe(default_bc_weekly_daily())
    null_dataframe = create_polars_dataframe([[]])

    # Test each DAO matrix getter
    load = dao.get_load(area_id)
    assert_frame_equal(load, default_scenario_hourly_dataframe, check_dtypes=False)

    solar = dao.get_solar(area_id)
    assert_frame_equal(solar, default_scenario_hourly_dataframe, check_dtypes=False)

    wind = dao.get_wind(area_id)
    assert_frame_equal(wind, default_scenario_hourly_dataframe, check_dtypes=False)

    misc_gen = dao.get_misc_gen(area_id)
    assert_frame_equal(misc_gen, default_8_fixed_hourly_dataframe, check_dtypes=False)

    reserves = dao.get_reserves(area_id)
    assert_frame_equal(reserves, default_4_fixed_hourly_dataframe, check_dtypes=False)

    link_series = dao.get_link_series(area_id, area2)
    assert_frame_equal(link_series, default_6_fixed_hourly_dataframe, check_dtypes=False)

    link_direct_capacity = dao.get_link_direct_capacities(area_id, area2)
    assert_frame_equal(link_direct_capacity, default_scenario_hourly_dataframe, check_dtypes=False)

    link_indirect_capacity = dao.get_link_indirect_capacities(area_id, area2)
    assert_frame_equal(link_indirect_capacity, default_scenario_hourly_dataframe, check_dtypes=False)

    thermal_prepro = dao.get_thermal_prepro(area_id, thermal_id)
    assert_frame_equal(thermal_prepro, default_data_dataframe, check_dtypes=False)

    thermal_modulation = dao.get_thermal_modulation(area_id, thermal_id)
    assert_frame_equal(thermal_modulation, default_modulation_dataframe, check_dtypes=False)

    thermal_series = dao.get_thermal_series(area_id, thermal_id)
    assert_frame_equal(thermal_series, default_scenario_hourly_dataframe, check_dtypes=False)

    thermal_fuel_cost = dao.get_thermal_fuel_cost(area_id, thermal_id)
    assert_frame_equal(thermal_fuel_cost, default_scenario_hourly_dataframe, check_dtypes=False)

    thermal_co2_cost = dao.get_thermal_co2_cost(area_id, thermal_id)
    assert_frame_equal(thermal_co2_cost, default_scenario_hourly_dataframe, check_dtypes=False)

    renewable_series = dao.get_renewable_series(area_id, renewable_id)
    assert_frame_equal(renewable_series, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_pmax_injection = dao.get_st_storage_pmax_injection(area_id, st_storage_id)
    assert_frame_equal(sts_pmax_injection, default_scenario_hourly_ones_dataframe, check_dtypes=False)

    sts_pmax_withdrawal = dao.get_st_storage_pmax_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_pmax_withdrawal, default_scenario_hourly_ones_dataframe, check_dtypes=False)

    sts_lower_rule_curve = dao.get_st_storage_lower_rule_curve(area_id, st_storage_id)
    assert_frame_equal(sts_lower_rule_curve, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_upper_rule_curve = dao.get_st_storage_upper_rule_curve(area_id, st_storage_id)
    assert_frame_equal(sts_upper_rule_curve, default_scenario_hourly_ones_dataframe, check_dtypes=False)

    sts_inflows = dao.get_st_storage_inflows(area_id, st_storage_id)
    assert_frame_equal(sts_inflows, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_cost_injection = dao.get_st_storage_cost_injection(area_id, st_storage_id)
    assert_frame_equal(sts_cost_injection, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_cost_withdrawal = dao.get_st_storage_cost_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_cost_withdrawal, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_cost_level = dao.get_st_storage_cost_level(area_id, st_storage_id)
    assert_frame_equal(sts_cost_level, default_cost_level_dataframe, check_dtypes=False)

    sts_cost_variation_injection = dao.get_st_storage_cost_variation_injection(area_id, st_storage_id)
    assert_frame_equal(sts_cost_variation_injection, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_cost_variation_withdrawal = dao.get_st_storage_cost_variation_withdrawal(area_id, st_storage_id)
    assert_frame_equal(sts_cost_variation_withdrawal, default_scenario_hourly_dataframe, check_dtypes=False)

    sts_constraint_matrix = dao.get_st_storage_additional_constraint_matrix(area_id, st_storage_id, constraint_id)
    assert_frame_equal(sts_constraint_matrix, default_scenario_hourly_dataframe, check_dtypes=False)

    hydro_maxpower = dao.get_hydro_maxpower(area_id)
    assert_frame_equal(hydro_maxpower, default_maxpower_dataframe, check_dtypes=False)

    hydro_reservoir = dao.get_hydro_reservoir(area_id)
    assert_frame_equal(hydro_reservoir, default_reservoir_dataframe, check_dtypes=False)

    hydro_energy = dao.get_hydro_energy(area_id)
    assert_frame_equal(hydro_energy, default_energy_dataframe, check_dtypes=False)

    hydro_run_of_river = dao.get_hydro_run_of_river(area_id)
    assert_frame_equal(hydro_run_of_river, default_scenario_hourly_dataframe, check_dtypes=False)

    hydro_modulation = dao.get_hydro_modulation(area_id)
    assert_frame_equal(hydro_modulation, default_scenario_daily_dataframe, check_dtypes=False)

    hydro_credit_modulations = dao.get_hydro_credit_modulations(area_id)
    assert_frame_equal(hydro_credit_modulations, default_credit_modulation_dataframe, check_dtypes=False)

    hydro_inflow_pattern = dao.get_hydro_inflow_pattern(area_id)
    assert_frame_equal(hydro_inflow_pattern, default_scenario_daily_dataframe, check_dtypes=False)

    hydro_water_values = dao.get_hydro_water_values(area_id)
    assert_frame_equal(hydro_water_values, default_water_values_dataframe, check_dtypes=False)

    hydro_mingen = dao.get_hydro_mingen(area_id)
    assert_frame_equal(hydro_mingen, default_scenario_hourly_dataframe, check_dtypes=False)

    hydro_max_hourly_gen_power = dao.get_hydro_max_hourly_gen_power(area_id)
    assert_frame_equal(hydro_max_hourly_gen_power, default_scenario_hourly_dataframe, check_dtypes=False)

    hydro_max_hourly_pump_power = dao.get_hydro_max_hourly_pump_power(area_id)
    assert_frame_equal(hydro_max_hourly_pump_power, default_scenario_hourly_dataframe, check_dtypes=False)

    hydro_max_daily_gen_energy = dao.get_hydro_max_daily_gen_energy(area_id)
    assert_frame_equal(hydro_max_daily_gen_energy, default_scenario_daily_dataframe, check_dtypes=False)

    hydro_max_daily_pump_energy = dao.get_hydro_max_daily_pump_energy(area_id)
    assert_frame_equal(hydro_max_daily_pump_energy, default_scenario_daily_dataframe, check_dtypes=False)

    xpansion_capacity = dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
    assert_frame_equal(xpansion_capacity, null_dataframe, check_dtypes=False)

    xpansion_weight = dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
    assert_frame_equal(xpansion_weight, null_dataframe, check_dtypes=False)

    bc_lt = dao.get_constraint_less_term_matrix(bc_both_id)
    assert_frame_equal(bc_lt, default_bc_hourly_dataframe, check_dtypes=False)

    bc_gt = dao.get_constraint_greater_term_matrix(bc_both_id)
    assert_frame_equal(bc_gt, default_bc_hourly_dataframe, check_dtypes=False)

    bc_eq = dao.get_constraint_equal_term_matrix(bc_eq_id)
    assert_frame_equal(bc_eq, default_bc_hourly_dataframe, check_dtypes=False)

    # Change the binding constraint timestep to ensure we get the right matrix
    dao.save_constraints([BindingConstraint(name=bc_eq_id, time_step=BindingConstraintFrequency.WEEKLY)])

    bc_eq = dao.get_constraint_equal_term_matrix(bc_eq_id)
    assert_frame_equal(bc_eq, default_bc_daily_weekly_dataframe, check_dtypes=False)


def test_empty_reserve_need_matrix(dao_10_0: StudyDao, matrix_service: ISimpleMatrixService) -> None:
    area_id = "paris"
    reserve_name = "R1"
    reserve_id = "r1"
    save_area(dao_10_0, area_id)
    dao_10_0.save_reserve_definitions({area_id: [build_reserve_definition(reserve_name)]})

    null_matrix_id = matrix_service.create(pl.DataFrame(orient="row"))
    dao_10_0.save_reserve_needs({area_id: {ReserveDefinitionId(reserve_id): null_matrix_id}})

    result = dao_10_0.get_reserve_need(area_id, reserve_id)
    assert_frame_equal(result, create_polars_dataframe(default_scenario_hourly()), check_dtypes=False)
