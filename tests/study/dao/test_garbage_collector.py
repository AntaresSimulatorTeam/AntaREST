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
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.database.database_matrices_provider import StudyDatabaseMatrixUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_garbage_collection(dao: DatabaseStudyDao, db_session: Session, tmp_path: Path) -> None:
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

    # Create matrices in the matrix-store
    # We need to use different contents, otherwise it will be enough that one table correctly prevents garbage
    # collection
    base_data = [[1, 2.5], [3, 4.7]]
    dataframes = [pl.DataFrame(data=[[a + i, b + i] for a, b in base_data], orient="row") for i in range(25)]
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
    ) = dataframes

    load_id = matrix_service.create(load_df)
    solar_id = matrix_service.create(solar_df)
    wind_id = matrix_service.create(wind_df)
    reserves_id = matrix_service.create(reserves_df)
    misc_gen_id = matrix_service.create(misc_gen_df)
    link_series_id = matrix_service.create(link_series_df)
    link_direct_id = matrix_service.create(link_direct_df)
    link_indirect_id = matrix_service.create(link_indirect_df)
    thermal_prepro_id = matrix_service.create(thermal_prepro_df)
    thermal_modulation_id = matrix_service.create(thermal_modulation_df)
    thermal_series_id = matrix_service.create(thermal_series_df)
    thermal_fuel_cost_id = matrix_service.create(thermal_fuel_cost_df)
    thermal_co2_cost_id = matrix_service.create(thermal_co2_cost_df)
    renewable_series_id = matrix_service.create(renewable_series_df)
    sts_pmax_injection_id = matrix_service.create(sts_pmax_injection_df)
    sts_pmax_withdrawal_id = matrix_service.create(sts_pmax_withdrawal_df)
    sts_lower_rule_curve_id = matrix_service.create(sts_lower_rule_curve_df)
    sts_upper_rule_curve_id = matrix_service.create(sts_upper_rule_curve_df)
    sts_inflows_id = matrix_service.create(sts_inflows_df)
    sts_cost_injection_id = matrix_service.create(sts_cost_injection_df)
    sts_cost_withdrawal_id = matrix_service.create(sts_cost_withdrawal_df)
    sts_cost_level_id = matrix_service.create(sts_cost_level_df)
    sts_cost_variation_injection_id = matrix_service.create(sts_cost_variation_injection_df)
    sts_cost_variation_withdrawal_id = matrix_service.create(sts_cost_variation_withdrawal_df)
    sts_constraint_matrix_id = matrix_service.create(sts_constraint_matrix_df)

    # Create `load`, `solar`, `wind`, `reserves` and `misc-gen` matrices in DB
    area_id = "paris"
    dao.save_area(area_id)
    dao.save_load(area_id, load_id)
    dao.save_solar(area_id, solar_id)
    dao.save_wind(area_id, wind_id)
    dao.save_reserves(area_id, reserves_id)
    dao.save_misc_gen(area_id, misc_gen_id)

    # Also create a link with `series`, `direct_capacity` and `indirect_capacity` matrices.
    area2 = "london"
    dao.save_area(area2)
    dao.save_link(Link(area1=area_id, area2=area2))
    dao.save_link_series(area_id, area2, link_series_id)
    dao.save_link_direct_capacities(area_id, area2, link_direct_id)
    dao.save_link_indirect_capacities(area_id, area2, link_indirect_id)

    # Create thermal cluster matrices
    thermal_id = "gas_cluster"
    dao.save_thermal(area_id, ThermalCluster(id=thermal_id, name="Gas Cluster"))
    dao.save_thermal_prepro(area_id, thermal_id, thermal_prepro_id)
    dao.save_thermal_modulation(area_id, thermal_id, thermal_modulation_id)
    dao.save_thermal_series(area_id, thermal_id, thermal_series_id)
    dao.save_thermal_fuel_cost(area_id, thermal_id, thermal_fuel_cost_id)
    dao.save_thermal_co2_cost(area_id, thermal_id, thermal_co2_cost_id)

    # Create renewable cluster matrices
    renewable_id = "battery"
    dao.save_renewable(area_id, RenewableCluster(id=renewable_id, name="Battery Fr"))
    dao.save_renewable_series(area_id, renewable_id, renewable_series_id)

    # Create ST Storage matrices
    st_storage_id = "battery_storage"
    dao.save_st_storage(area_id, STStorage(id=st_storage_id, name="Battery Storage"))
    dao.save_st_storage_pmax_injection(area_id, st_storage_id, sts_pmax_injection_id)
    dao.save_st_storage_pmax_withdrawal(area_id, st_storage_id, sts_pmax_withdrawal_id)
    dao.save_st_storage_lower_rule_curve(area_id, st_storage_id, sts_lower_rule_curve_id)
    dao.save_st_storage_upper_rule_curve(area_id, st_storage_id, sts_upper_rule_curve_id)
    dao.save_st_storage_inflows(area_id, st_storage_id, sts_inflows_id)
    dao.save_st_storage_cost_injection(area_id, st_storage_id, sts_cost_injection_id)
    dao.save_st_storage_cost_withdrawal(area_id, st_storage_id, sts_cost_withdrawal_id)
    dao.save_st_storage_cost_level(area_id, st_storage_id, sts_cost_level_id)
    dao.save_st_storage_cost_variation_injection(area_id, st_storage_id, sts_cost_variation_injection_id)
    dao.save_st_storage_cost_variation_withdrawal(area_id, st_storage_id, sts_cost_variation_withdrawal_id)

    # Create ST Storage additional constraint matrix
    constraint_id = "constraint_1"
    dao.save_st_storage_additional_constraints(
        area_id,
        storage_id=st_storage_id,
        constraints=[STStorageAdditionalConstraint(id=constraint_id, name="Constraint 1")],
    )
    dao.save_st_storage_constraint_matrix(area_id, st_storage_id, constraint_id, sts_constraint_matrix_id)

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
