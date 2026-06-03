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
import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import polars as pl
import pytest
from antares.study.version import StudyVersion
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from antarest.blobstore.service import IBlobService
from antarest.core.interfaces.cache import ICache
from antarest.dbmodel import Base
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintOperator,
    ConstraintId,
)
from antarest.study.business.model.config.optimization_config_model import (
    initialize_optimization_preferences_against_version,
)
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint, initialize_st_storage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import (
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
    STUDY_VERSION_10_0,
    Study,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.conftest import build_db_dao, build_filesystem_dao
from tests.study.dao.utils import save_area


@pytest.fixture
def db_dao(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def db_dao_930(db_dao_930_and_matrix_service) -> DatabaseStudyDao:
    return db_dao_930_and_matrix_service[0]


@pytest.fixture
def db_dao_930_and_matrix_service(
    db_session: Session, matrix_service: ISimpleMatrixService
) -> tuple[DatabaseStudyDao, ISimpleMatrixService]:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3), matrix_service


@pytest.fixture
def fs_dao_930_and_matrix_service(
    db_session: Session, command_context: CommandContext, tmp_path: Path, core_cache: ICache
) -> tuple[FileStudyTreeDao, ISimpleMatrixService]:
    return build_fs_dao(db_session, STUDY_VERSION_9_3, command_context, core_cache, tmp_path)


@pytest.fixture(scope="session")
def db_dao_930_shared() -> DatabaseStudyDao:
    return build_shared_db_dao(STUDY_VERSION_9_3, InMemorySimpleMatrixService())


def build_shared_db_dao(study_version: StudyVersion, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    """To be used inside tests that do not alter the DAO, but just use it"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine)
    with contextlib.closing(make_session()) as session:
        return build_db_dao(session, matrix_service, study_version)


@pytest.fixture
def db_dao_920(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_2)


def build_fs_dao(
    db_session: Session,
    version: StudyVersion,
    command_context: "CommandContext",
    core_cache: "ICache",
    tmp_path: Path,
) -> tuple[FileStudyTreeDao, ISimpleMatrixService]:
    matrix_service = command_context.matrix_service
    study_factory = StudyFactory(matrix_service=matrix_service, cache=core_cache)
    return build_filesystem_dao(db_session, version, command_context, study_factory, tmp_path), matrix_service


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    core_cache: "ICache",
) -> StudyDao:
    """A DAO parameterized over both backends (v8.8+)."""
    if request.param == "db":
        return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    else:
        dao, _ = build_fs_dao(db_session, STUDY_VERSION_8_8, command_context, core_cache, tmp_path)
        return dao


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao_builder(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    core_cache: "ICache",
) -> Callable[[StudyVersion], StudyDao]:
    """A DAO factory parameterized over both backends, accepting the study version as argument."""

    def _build(version: StudyVersion) -> StudyDao:
        if request.param == "db":
            return build_db_dao(db_session, matrix_service, version)
        dao, _ = build_fs_dao(db_session, version, command_context, core_cache, tmp_path)
        return dao

    return _build


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao_and_matrix_service(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    core_cache: "ICache",
) -> tuple[StudyDao, ISimpleMatrixService]:
    """A (DAO, matrix_service) pair parameterized over both backends (v9.3)."""
    if request.param == "db":
        return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3), matrix_service
    else:
        return build_fs_dao(db_session, STUDY_VERSION_9_3, command_context, core_cache, tmp_path)


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao_10_0(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    core_cache: "ICache",
) -> StudyDao:
    """A DAO parameterized over both backends (v10.0)."""
    # v10.0 has no study template on disk — create a v9.3 study and force its version to 10.0.
    if request.param == "db":
        dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
        study = db_session.get(Study, dao.get_study_id())
        study.version = str(STUDY_VERSION_10_0)
        db_session.commit()
        # Settings were saved at v9.3; replay v10 init so v10-specific defaults stick.
        prefs = dao.get_optimization_preferences()
        initialize_optimization_preferences_against_version(prefs, STUDY_VERSION_10_0)
        dao.save_optimization_preferences(prefs)
        return dao
    else:
        dao, _ = build_fs_dao(db_session, STUDY_VERSION_9_3, command_context, core_cache, tmp_path)
        dao.get_file_study().config.version = STUDY_VERSION_10_0
        return dao


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao_860_and_matrix_service(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    core_cache: "ICache",
) -> tuple[StudyDao, ISimpleMatrixService]:
    """A (DAO, matrix_service) pair parameterized over both backends (v8.6)."""
    if request.param == "db":
        return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_6), matrix_service
    else:
        return build_fs_dao(db_session, STUDY_VERSION_8_6, command_context, core_cache, tmp_path)


def build_reserve_definition(reserve_id: str) -> ReserveDefinition:
    return ReserveDefinition(
        id=reserve_id,
        type=ReserveType.UP,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )


@dataclass
class RealCaseStudy:
    area1: str
    area2: str
    thermal_id: str
    renewable_id: str
    sts_id: str
    sts_constraint_id: str
    bc_both_id: ConstraintId
    bc_eq_id: ConstraintId
    dataframes: list[pl.DataFrame]


def build_real_case_study(
    dao: StudyDao, matrix_service: ISimpleMatrixService, null_matrices: bool = False
) -> RealCaseStudy:
    """
    If `null_matrices` is True, the created matrices will all be the same empty matrix.
    Otherwise, the matrices will be created with different contents to diversify tests.
    """
    if null_matrices:
        dataframes = [pl.DataFrame(orient="row")] * 43
    else:
        base_data = [[1, 2.5], [3, 4.7]]
        dataframes = [pl.DataFrame(data=[[a + i, b + i] for a, b in base_data], orient="row") for i in range(43)]

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
    xpansion_capacity_id = matrix_service.create(xpansion_capacity_df)
    xpansion_weight_id = matrix_service.create(xpansion_weight_df)

    # Create `load`, `solar`, `wind`, `reserves` and `misc-gen` matrices in DB
    area_id = "paris"
    save_area(dao, area_id)
    dao.save_load({area_id: load_id})
    dao.save_solar({area_id: solar_id})
    dao.save_wind({area_id: wind_id})
    dao.save_reserves({area_id: reserves_id})
    dao.save_misc_gen({area_id: misc_gen_id})

    # Also create a link with `series`, `direct_capacity` and `indirect_capacity` matrices.
    area2 = "london"
    save_area(dao, area2)
    dao.save_links([Link(area1=area_id, area2=area2)])
    dao.save_link_series({(area_id, area2): link_series_id})
    dao.save_link_direct_capacities({(area_id, area2): link_direct_id})
    dao.save_link_indirect_capacities({(area_id, area2): link_indirect_id})

    # Create thermal cluster matrices
    thermal_id = "gas_cluster"
    thermal = ThermalCluster(id=thermal_id, name="Gas Cluster")
    initialize_thermal_cluster(thermal, dao.get_version())
    dao.save_thermals({area_id: [thermal]})
    dao.save_thermal_prepro({area_id: {thermal_id: thermal_prepro_id}})
    dao.save_thermal_modulation({area_id: {thermal_id: thermal_modulation_id}})
    dao.save_thermal_series({area_id: {thermal_id: thermal_series_id}})
    dao.save_thermal_fuel_cost({area_id: {thermal_id: thermal_fuel_cost_id}})
    dao.save_thermal_co2_cost({area_id: {thermal_id: thermal_co2_cost_id}})

    # Create renewable cluster matrices
    renewable_id = "battery"
    dao.save_renewable(area_id, RenewableCluster(id=renewable_id, name="Battery Fr"))
    dao.save_renewable_series({area_id: {renewable_id: renewable_series_id}})

    # Create ST Storage matrices
    st_storage_id = "battery_storage"
    storage = STStorage(id=st_storage_id, name="Battery Storage")
    initialize_st_storage(storage, dao.get_version())
    dao.save_st_storages({area_id: [storage]})
    dao.save_st_storage_pmax_injection({area_id: {st_storage_id: sts_pmax_injection_id}})
    dao.save_st_storage_pmax_withdrawal({area_id: {st_storage_id: sts_pmax_withdrawal_id}})
    dao.save_st_storage_lower_rule_curve({area_id: {st_storage_id: sts_lower_rule_curve_id}})
    dao.save_st_storage_upper_rule_curve({area_id: {st_storage_id: sts_upper_rule_curve_id}})
    dao.save_st_storage_inflows({area_id: {st_storage_id: sts_inflows_id}})
    dao.save_st_storage_cost_injection({area_id: {st_storage_id: sts_cost_injection_id}})
    dao.save_st_storage_cost_withdrawal({area_id: {st_storage_id: sts_cost_withdrawal_id}})
    dao.save_st_storage_cost_level({area_id: {st_storage_id: sts_cost_level_id}})
    dao.save_st_storage_cost_variation_injection({area_id: {st_storage_id: sts_cost_variation_injection_id}})
    dao.save_st_storage_cost_variation_withdrawal({area_id: {st_storage_id: sts_cost_variation_withdrawal_id}})

    # Create ST Storage additional constraint matrix
    constraint_id = "constraint_1"
    dao.save_st_storage_additional_constraints(
        {area_id: {st_storage_id: [STStorageAdditionalConstraint(id=constraint_id, name="Constraint 1")]}},
    )
    dao.save_st_storage_constraint_matrices({area_id: {st_storage_id: {constraint_id: sts_constraint_matrix_id}}})

    # Create hydro matrices
    dao.save_hydro_maxpower({area_id: hydro_maxpower_id})
    dao.save_hydro_reservoir({area_id: hydro_reservoir_id})
    dao.save_hydro_energy({area_id: hydro_energy_id})
    dao.save_hydro_run_of_river({area_id: hydro_run_of_river_id})
    dao.save_hydro_modulation({area_id: hydro_modulation_id})
    dao.save_hydro_credit_modulations({area_id: hydro_credit_modulations_id})
    dao.save_hydro_inflow_pattern({area_id: hydro_inflow_pattern_id})
    dao.save_hydro_water_values({area_id: hydro_water_values_id})
    dao.save_hydro_mingen({area_id: hydro_mingen_id})
    dao.save_hydro_max_hourly_gen_power({area_id: hydro_max_hourly_gen_power_id})
    dao.save_hydro_max_hourly_pump_power({area_id: hydro_max_hourly_pump_power_id})
    dao.save_hydro_max_daily_gen_energy({area_id: hydro_max_daily_gen_energy_id})
    dao.save_hydro_max_daily_pump_energy({area_id: hydro_max_daily_pump_energy_id})

    # Create xpansion capacity and weight matrices
    dao.create_xpansion_configuration()
    dao.save_xpansion_capacity({"link_capa.txt": xpansion_capacity_id})
    dao.save_xpansion_weight({"mc_weights.csv": xpansion_weight_id})

    # Create binding constraint matrices — covers LT, GT, and EQ tables
    bc_lt_matrix_id = matrix_service.create(bc_lt_df)
    bc_gt_matrix_id = matrix_service.create(bc_gt_df)
    bc_eq_matrix_id = matrix_service.create(bc_eq_df)
    bc_both_id = "bc_both"
    bc_equal_id = "bc_equal"
    dao.save_constraints(
        [
            BindingConstraint(id=bc_both_id, name=bc_both_id, operator=BindingConstraintOperator.BOTH),
            BindingConstraint(id=bc_equal_id, name=bc_equal_id, operator=BindingConstraintOperator.EQUAL),
        ]
    )
    dao.save_constraint_less_term_matrix({bc_both_id: bc_lt_matrix_id})
    dao.save_constraint_greater_term_matrix({bc_both_id: bc_gt_matrix_id})
    dao.save_constraint_equal_term_matrix({bc_equal_id: bc_eq_matrix_id})

    return RealCaseStudy(
        area1=area_id,
        area2=area2,
        thermal_id=thermal_id,
        renewable_id=renewable_id,
        sts_id=st_storage_id,
        sts_constraint_id=constraint_id,
        bc_both_id=bc_both_id,
        bc_eq_id=bc_equal_id,
        dataframes=dataframes,
    )


def create_area(area_name: str, dao: StudyDao) -> None:
    constants = dao.generator_matrix_constants
    command_context = CommandContext(
        generator_matrix_constants=constants, matrix_service=dao.matrix_service, blob_service=Mock(spec=IBlobService)
    )

    command = CreateArea(area_name=area_name, command_context=command_context, study_version=dao.get_version())
    output = command.apply(dao)
    assert output.status
