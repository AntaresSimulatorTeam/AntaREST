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
from unittest.mock import Mock

import polars as pl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from antarest.blobstore.service import IBlobService
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
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.system import GemsSystem
from antarest.study.business.model.gems.taxonomy import GemsTaxonomy
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint, initialize_st_storage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import (
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
    STUDY_VERSION_10_2,
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
def db_dao_920(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_2)


@pytest.fixture
def db_dao_930(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)


@pytest.fixture(scope="session")
def db_dao_930_shared() -> DatabaseStudyDao:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine)
    with contextlib.closing(make_session()) as session:
        return build_db_dao(session, InMemorySimpleMatrixService(), STUDY_VERSION_9_3)


def build_db_dao_10_2(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    """Initialize a v10.2 study using the latest available reference template."""
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    study = db_session.get(Study, dao.get_study_id())
    assert study is not None
    study.version = str(STUDY_VERSION_10_2)
    db_session.commit()
    # Settings were saved at v9.3; replay v10 init so v10-specific defaults stick.
    prefs = dao.get_optimization_preferences()
    initialize_optimization_preferences_against_version(prefs, STUDY_VERSION_10_2)
    dao.save_optimization_preferences(prefs)
    return dao


@pytest.fixture(params=["db", "fs"], ids=["database", "filesystem"])
def dao_10_2(
    request,
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    command_context: "CommandContext",
    tmp_path: Path,
    study_factory: StudyFactory,
) -> StudyDao:
    """A DAO parameterized over both backends (v10.2)."""
    # v10.2 has no study template on disk — create a v9.3 study and force its version to 10.2.
    if request.param == "db":
        return build_db_dao_10_2(db_session, matrix_service)
    else:
        dao = build_filesystem_dao(db_session, STUDY_VERSION_9_3, command_context, study_factory, tmp_path)
        dao.get_file_study().config.version = STUDY_VERSION_10_2
        return dao


def build_reserve_definition(reserve_name: str) -> ReserveDefinition:
    return ReserveDefinition(
        name=reserve_name,
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


def build_real_case_study(dao: StudyDao, null_matrices: bool = False) -> RealCaseStudy:
    """
    If `null_matrices` is True, the created matrices will all be the same empty matrix.
    Otherwise, the matrices will be created with different contents to diversify tests.
    """
    matrix_service = dao.matrix_service
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


def check_8_1_gems_library_integrity(library: GemsLibrary) -> None:
    # Metadata
    assert library is not None
    assert library.id == "andromede-v1-models-weo-hybrid"
    assert (
        library.description
        == "Andromede V1 model library - without expectation operators - allows hybrid connections (i.e. connections between Andromede models and Antares legacy area)"
    )
    assert library.version is None
    # Port types
    assert len(library.port_types) == 1
    port_type = library.port_types[0]
    assert port_type.id == "flow"
    assert port_type.description == "A port which transfers power flow"
    assert len(port_type.fields) == 1
    assert port_type.fields[0].id == "flow"
    assert port_type.thermal_capacity_connection is None
    assert port_type.area_connection is not None
    assert port_type.area_connection.spillage_bound is None
    assert port_type.area_connection.injection_to_balance == "flow"
    assert port_type.area_connection.unsupplied_energy_bound is None
    # Models
    assert len(library.models) == 2
    first_model = library.models[0]
    assert first_model.id == "dsr"
    assert first_model.description is None
    assert first_model.taxonomy_category is None
    assert first_model.properties == []
    assert len(first_model.parameters) == 2
    assert first_model.parameters[0].id == "curtailment_price"
    assert first_model.parameters[0].time_dependent is False
    assert first_model.parameters[0].scenario_dependent is False
    assert first_model.parameters[1].id == "max_load"
    assert first_model.parameters[1].time_dependent is True
    assert first_model.parameters[1].scenario_dependent is True
    assert len(first_model.ports) == 1
    assert first_model.ports[0].id == "balance_port"
    assert first_model.ports[0].type == "flow"
    second_model = library.models[1]
    assert second_model.id == "electrolyser"
    assert second_model.description is None
    assert second_model.taxonomy_category is None
    assert second_model.properties == []
    assert len(second_model.parameters) == 2
    assert second_model.parameters[0].id == "efficiency"
    assert second_model.parameters[0].time_dependent is False
    assert second_model.parameters[0].scenario_dependent is False
    assert second_model.parameters[1].id == "p_max"
    assert second_model.parameters[1].time_dependent is True
    assert second_model.parameters[1].scenario_dependent is True
    assert len(second_model.ports) == 2
    assert second_model.ports[0].id == "hydrogen_port"
    assert second_model.ports[0].type == "flow"
    assert second_model.ports[1].id == "power_port"
    assert second_model.ports[1].type == "flow"


def check_gems_system_integrity(system: GemsSystem) -> None:
    assert system is not None
    assert system.id == "System 8_1"
    assert system.description == "Electrolyser - V8.6"
    assert len(system.components) == 1

    first_component = system.components[0]
    assert first_component.id == "electrolyser"
    assert first_component.model == "andromede-v1-models-weo-hybrid.electrolyser"
    assert first_component.scenario_group == "sg1"
    assert first_component.parameters is not None
    assert len(first_component.parameters) == 2
    assert first_component.parameters[0].id == "efficiency"
    assert first_component.parameters[0].time_dependent is False
    assert first_component.parameters[0].scenario_dependent is False
    assert first_component.parameters[0].value == 0.7
    assert first_component.parameters[1].id == "p_max"
    assert first_component.parameters[1].time_dependent is False
    assert first_component.parameters[1].scenario_dependent is False
    assert first_component.parameters[1].value == 300


def check_gems_taxonomy_integrity(taxonomy: GemsTaxonomy) -> None:
    assert taxonomy is not None
    assert taxonomy.id == "antares_legacy_taxonomy"
    assert taxonomy.description == "GEMS taxonomy configuration for Antares Legacy Models."
    assert len(taxonomy.categories) == 15

    categories_by_id = {c.id: c for c in taxonomy.categories}
    assert sorted(list(categories_by_id)) == [
        "balance",
        "capacity_investment_decisions",
        "consumption",
        "coupling_models",
        "dispatchable_generation",
        "fatal_consumption",
        "fatal_generation",
        "generation",
        "link",
        "long_term_storage",
        "long_term_storage_with_watervalues",
        "miscellaneous_fatal_generation",
        "renewable_fatal_generation",
        "short_term_storage",
        "storage",
    ]

    balance = categories_by_id["balance"]
    assert balance.id == "balance"
    assert balance.parent_category is None
    assert balance.variables == [{"id": "unsupplied_energy"}, {"id": "spilled_energy"}]
    assert balance.ports == [{"id": "balance_port"}]
    assert balance.binding_constraints == [{"id": "balance"}]
    assert balance.extra_outputs is not None
    assert len(balance.extra_outputs) == 5

    generation = categories_by_id["generation"]
    assert generation.id == "generation"
    assert generation.parent_category is None
    assert generation.ports == [{"id": "balance_port"}]

    dispatchable = categories_by_id["dispatchable_generation"]
    assert dispatchable.id == "dispatchable_generation"
    assert dispatchable.parent_category == "generation"
    assert dispatchable.variables == [{"id": "generation_power"}]
    assert dispatchable.properties == [{"id": "technology"}]
