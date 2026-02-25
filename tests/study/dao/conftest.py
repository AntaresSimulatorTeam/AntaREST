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
import uuid
from dataclasses import dataclass

import polars as pl
import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3, StorageMode
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.helpers import create_study


def build_dao(db_session: Session, matrix_service: ISimpleMatrixService, version: StudyVersion) -> DatabaseStudyDao:
    """
    Create a test study in database mode and create a DatabaseStudyDao instance for testing.
    """
    study_id = str(uuid.uuid4())
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    with db_session:
        study = create_study(id=study_id, name="Test Study", version=str(version))
        study.storage_mode = StorageMode.DATABASE
        db_session.add(study)
        db_session.commit()
        factory = DatabaseStudyDaoFactory(matrix_service, generator_matrix_constants, db_session)
        dao = factory.create_study_dao(study)
    return dao


@pytest.fixture
def dao(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def dao_930(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_9_3)


@pytest.fixture
def dao_920(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_9_2)


@dataclass
class RealCaseDBStudy:
    area1: str
    area2: str
    thermal_id: str
    renewable_id: str
    sts_id: str
    sts_constraint_id: str
    dataframes: list[pl.DataFrame]


def build_real_case_db_study(dao: DatabaseStudyDao) -> RealCaseDBStudy:
    matrix_service = dao._matrix_service
    # Create matrices in the matrix-store with different contents to diversify tests.
    base_data = [[1, 2.5], [3, 4.7]]
    dataframes = [pl.DataFrame(data=[[a + i, b + i] for a, b in base_data], orient="row") for i in range(38)]
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
    hydro_maxpower_id = matrix_service.create(hydro_maxpower_df)
    hydro_reservoir_id = matrix_service.create(hydro_reservoir_df)
    hydro_energy_id = matrix_service.create(hydro_energy_df)
    hydro_run_of_river_id = matrix_service.create(hydro_run_of_river_df)
    hydro_modulation_id = matrix_service.create(hydro_modulation_df)
    hydro_credit_modulations_id = matrix_service.create(hydro_credit_modulations_df)
    hydro_inflow_pattern_id = matrix_service.create(hydro_inflow_pattern_df)
    hydro_water_values_id = matrix_service.create(hydro_water_values_df)
    hydro_mingen_id = matrix_service.create(hydro_mingen_df)
    hydro_max_hourly_gen_power_id = matrix_service.create(hydro_max_hourly_gen_power_df)
    hydro_max_hourly_pump_power_id = matrix_service.create(hydro_max_hourly_pump_power_df)
    hydro_max_daily_gen_energy_id = matrix_service.create(hydro_max_daily_gen_energy_df)
    hydro_max_daily_pump_energy_id = matrix_service.create(hydro_max_daily_pump_energy_df)

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

    # Create hydro matrices
    dao.save_hydro_maxpower(area_id, hydro_maxpower_id)
    dao.save_hydro_reservoir(area_id, hydro_reservoir_id)
    dao.save_hydro_energy(area_id, hydro_energy_id)
    dao.save_hydro_run_of_river(area_id, hydro_run_of_river_id)
    dao.save_hydro_modulation(area_id, hydro_modulation_id)
    dao.save_hydro_credit_modulations(area_id, hydro_credit_modulations_id)
    dao.save_hydro_inflow_pattern(area_id, hydro_inflow_pattern_id)
    dao.save_hydro_water_values(area_id, hydro_water_values_id)
    dao.save_hydro_mingen(area_id, hydro_mingen_id)
    dao.save_hydro_max_hourly_gen_power(area_id, hydro_max_hourly_gen_power_id)
    dao.save_hydro_max_hourly_pump_power(area_id, hydro_max_hourly_pump_power_id)
    dao.save_hydro_max_daily_gen_energy(area_id, hydro_max_daily_gen_energy_id)
    dao.save_hydro_max_daily_pump_energy(area_id, hydro_max_daily_pump_energy_id)

    return RealCaseDBStudy(
        area1=area_id,
        area2=area2,
        thermal_id=thermal_id,
        renewable_id=renewable_id,
        sts_id=st_storage_id,
        sts_constraint_id=constraint_id,
        dataframes=dataframes,
    )
