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
from pathlib import Path
from unittest.mock import Mock

import polars as pl
from sqlalchemy.orm import Session

from antarest.core.config import InternalMatrixFormat
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.dao.database.database_matrices_provider import StudyDatabaseMatrixUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_10_0
from tests.study.dao.conftest import build_db_dao, build_real_case_study, build_reserve_definition
from tests.study.dao.utils import save_area


def test_garbage_collection(db_dao: DatabaseStudyDao, db_session: Session, tmp_path: Path) -> None:
    dao = db_dao
    # Create a real matrix_service
    bucket_dir = tmp_path / "matrix_store"
    matrix_service = MatrixService(
        repo=MatrixRepository(db_session),
        repo_dataset=MatrixDataSetRepository(db_session),
        matrix_content_repository=MatrixContentRepository(bucket_dir, InternalMatrixFormat.FEATHER),
        file_transfer_manager=Mock(),
        task_service=Mock(),
        config=Mock(),
        user_service=Mock(),
    )
    dao._matrix_service = matrix_service

    # Register the DB provider
    provider = StudyDatabaseMatrixUsageProvider(matrix_service)
    matrix_service.register_usage_provider(provider)

    result = build_real_case_study(dao, matrix_service)
    (
        load_df,
        solar_df,
        wind_df,
        reserves_df,
        misc_gen_df,
        link_series_df,
        link_direct_df,
        link_indirect_df,
        thermal_prepro_df,
        thermal_modulation_df,
        thermal_series_df,
        thermal_fuel_cost_df,
        thermal_co2_cost_df,
        renewable_series_df,
        sts_pmax_injection_df,
        sts_pmax_withdrawal_df,
        sts_lower_rule_curve_df,
        sts_upper_rule_curve_df,
        sts_inflows_df,
        sts_cost_injection_df,
        sts_cost_withdrawal_df,
        sts_cost_level_df,
        sts_cost_variation_injection_df,
        sts_cost_variation_withdrawal_df,
        sts_constraint_matrix_df,
        hydro_maxpower_df,
        hydro_reservoir_df,
        hydro_energy_df,
        hydro_run_of_river_df,
        hydro_modulation_df,
        hydro_credit_modulations_df,
        hydro_inflow_pattern_df,
        hydro_water_values_df,
        hydro_mingen_df,
        hydro_max_hourly_gen_power_df,
        hydro_max_hourly_pump_power_df,
        hydro_max_daily_gen_energy_df,
        hydro_max_daily_pump_energy_df,
        xpansion_capacity_df,
        xpansion_weight_df,
        bc_lt_df,
        bc_gt_df,
        bc_eq_df,
    ) = result.dataframes
    area_id, area2 = result.area1, result.area2
    thermal_id, renewable_id, st_storage_id = result.thermal_id, result.renewable_id, result.sts_id
    constraint_id = result.sts_constraint_id
    bc_both_id, bc_eq_id = result.bc_both_id, result.bc_eq_id

    # Launch the Garbage collection
    task = clean_matrices(matrix_service=matrix_service, dry_run=False, retention_time=0)
    assert task.status == BackGroundTaskStatus.SUCCESS
    assert task.deleted_count == 0

    # Ensures the matrices were not removed from their tables
    load = dao.get_load(area_id)
    pl.testing.assert_frame_equal(load, load_df, check_dtypes=False)

    solar = dao.get_solar(area_id)
    pl.testing.assert_frame_equal(solar, solar_df, check_dtypes=False)

    wind = dao.get_wind(area_id)
    pl.testing.assert_frame_equal(wind, wind_df, check_dtypes=False)

    misc_gen = dao.get_misc_gen(area_id)
    pl.testing.assert_frame_equal(misc_gen, misc_gen_df, check_dtypes=False)

    reserves = dao.get_reserves(area_id)
    pl.testing.assert_frame_equal(reserves, reserves_df, check_dtypes=False)

    link_series = dao.get_link_series(area_id, area2)
    pl.testing.assert_frame_equal(link_series, link_series_df, check_dtypes=False)

    link_direct_capacity = dao.get_link_direct_capacities(area_id, area2)
    pl.testing.assert_frame_equal(link_direct_capacity, link_direct_df, check_dtypes=False)

    link_indirect_capacity = dao.get_link_indirect_capacities(area_id, area2)
    pl.testing.assert_frame_equal(link_indirect_capacity, link_indirect_df, check_dtypes=False)

    thermal_prepro = dao.get_thermal_prepro(area_id, thermal_id)
    pl.testing.assert_frame_equal(thermal_prepro, thermal_prepro_df, check_dtypes=False)

    thermal_modulation = dao.get_thermal_modulation(area_id, thermal_id)
    pl.testing.assert_frame_equal(thermal_modulation, thermal_modulation_df, check_dtypes=False)

    thermal_series = dao.get_thermal_series(area_id, thermal_id)
    pl.testing.assert_frame_equal(thermal_series, thermal_series_df, check_dtypes=False)

    thermal_fuel_cost = dao.get_thermal_fuel_cost(area_id, thermal_id)
    pl.testing.assert_frame_equal(thermal_fuel_cost, thermal_fuel_cost_df, check_dtypes=False)

    thermal_co2_cost = dao.get_thermal_co2_cost(area_id, thermal_id)
    pl.testing.assert_frame_equal(thermal_co2_cost, thermal_co2_cost_df, check_dtypes=False)

    renewable_series = dao.get_renewable_series(area_id, renewable_id)
    pl.testing.assert_frame_equal(renewable_series, renewable_series_df, check_dtypes=False)

    sts_pmax_injection = dao.get_st_storage_pmax_injection(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_pmax_injection, sts_pmax_injection_df, check_dtypes=False)

    sts_pmax_withdrawal = dao.get_st_storage_pmax_withdrawal(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_pmax_withdrawal, sts_pmax_withdrawal_df, check_dtypes=False)

    sts_lower_rule_curve = dao.get_st_storage_lower_rule_curve(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_lower_rule_curve, sts_lower_rule_curve_df, check_dtypes=False)

    sts_upper_rule_curve = dao.get_st_storage_upper_rule_curve(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_upper_rule_curve, sts_upper_rule_curve_df, check_dtypes=False)

    sts_inflows = dao.get_st_storage_inflows(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_inflows, sts_inflows_df, check_dtypes=False)

    sts_cost_injection = dao.get_st_storage_cost_injection(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_cost_injection, sts_cost_injection_df, check_dtypes=False)

    sts_cost_withdrawal = dao.get_st_storage_cost_withdrawal(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_cost_withdrawal, sts_cost_withdrawal_df, check_dtypes=False)

    sts_cost_level = dao.get_st_storage_cost_level(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_cost_level, sts_cost_level_df, check_dtypes=False)

    sts_cost_variation_injection = dao.get_st_storage_cost_variation_injection(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_cost_variation_injection, sts_cost_variation_injection_df, check_dtypes=False)

    sts_cost_variation_withdrawal = dao.get_st_storage_cost_variation_withdrawal(area_id, st_storage_id)
    pl.testing.assert_frame_equal(sts_cost_variation_withdrawal, sts_cost_variation_withdrawal_df, check_dtypes=False)

    sts_constraint_matrix = dao.get_st_storage_additional_constraint_matrix(area_id, st_storage_id, constraint_id)
    pl.testing.assert_frame_equal(sts_constraint_matrix, sts_constraint_matrix_df, check_dtypes=False)

    hydro_maxpower = dao.get_hydro_maxpower(area_id)
    pl.testing.assert_frame_equal(hydro_maxpower, hydro_maxpower_df, check_dtypes=False)

    hydro_reservoir = dao.get_hydro_reservoir(area_id)
    pl.testing.assert_frame_equal(hydro_reservoir, hydro_reservoir_df, check_dtypes=False)

    hydro_energy = dao.get_hydro_energy(area_id)
    pl.testing.assert_frame_equal(hydro_energy, hydro_energy_df, check_dtypes=False)

    hydro_run_of_river = dao.get_hydro_run_of_river(area_id)
    pl.testing.assert_frame_equal(hydro_run_of_river, hydro_run_of_river_df, check_dtypes=False)

    hydro_modulation = dao.get_hydro_modulation(area_id)
    pl.testing.assert_frame_equal(hydro_modulation, hydro_modulation_df, check_dtypes=False)

    hydro_credit_modulations = dao.get_hydro_credit_modulations(area_id)
    pl.testing.assert_frame_equal(hydro_credit_modulations, hydro_credit_modulations_df, check_dtypes=False)

    hydro_inflow_pattern = dao.get_hydro_inflow_pattern(area_id)
    pl.testing.assert_frame_equal(hydro_inflow_pattern, hydro_inflow_pattern_df, check_dtypes=False)

    hydro_water_values = dao.get_hydro_water_values(area_id)
    pl.testing.assert_frame_equal(hydro_water_values, hydro_water_values_df, check_dtypes=False)

    hydro_mingen = dao.get_hydro_mingen(area_id)
    pl.testing.assert_frame_equal(hydro_mingen, hydro_mingen_df, check_dtypes=False)

    hydro_max_hourly_gen_power = dao.get_hydro_max_hourly_gen_power(area_id)
    pl.testing.assert_frame_equal(hydro_max_hourly_gen_power, hydro_max_hourly_gen_power_df, check_dtypes=False)

    hydro_max_hourly_pump_power = dao.get_hydro_max_hourly_pump_power(area_id)
    pl.testing.assert_frame_equal(hydro_max_hourly_pump_power, hydro_max_hourly_pump_power_df, check_dtypes=False)

    hydro_max_daily_gen_energy = dao.get_hydro_max_daily_gen_energy(area_id)
    pl.testing.assert_frame_equal(hydro_max_daily_gen_energy, hydro_max_daily_gen_energy_df, check_dtypes=False)

    hydro_max_daily_pump_energy = dao.get_hydro_max_daily_pump_energy(area_id)
    pl.testing.assert_frame_equal(hydro_max_daily_pump_energy, hydro_max_daily_pump_energy_df, check_dtypes=False)

    xpansion_capacity = dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
    pl.testing.assert_frame_equal(xpansion_capacity, xpansion_capacity_df, check_dtypes=False)

    xpansion_weight = dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
    pl.testing.assert_frame_equal(xpansion_weight, xpansion_weight_df, check_dtypes=False)

    bc_lt = dao.get_constraint_less_term_matrix(bc_both_id)
    pl.testing.assert_frame_equal(bc_lt, bc_lt_df, check_dtypes=False)

    bc_gt = dao.get_constraint_greater_term_matrix(bc_both_id)
    pl.testing.assert_frame_equal(bc_gt, bc_gt_df, check_dtypes=False)

    bc_eq = dao.get_constraint_equal_term_matrix(bc_eq_id)
    pl.testing.assert_frame_equal(bc_eq, bc_eq_df, check_dtypes=False)


def test_provider_includes_reserve_need_matrix(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """The reserve_need matrix must be reported as in-use so the GC won't remove it."""
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_10_0)
    save_area(dao, "paris")
    dao.save_reserve_definitions({"paris": [build_reserve_definition("R1")]})
    matrix_id = matrix_service.create(pl.DataFrame([[0.0]] * 8760, orient="row"))
    dao.save_reserve_needs({"paris": {ReserveDefinitionId("R1"): matrix_id}})

    with db():
        provider = StudyDatabaseMatrixUsageProvider(matrix_service)
        used_ids = {ref.matrix_id for ref in provider.get_matrix_usage()}
    assert matrix_id in used_ids
