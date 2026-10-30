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
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from antarest.core.exceptions import (
    GemsConnectedObjectDeletionNotAllowed,
    GemsInvalidConnection,
    GemsInvalidParameterValue,
    GemsParameterNotFound,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.dbmodel import Base
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.business.model.gems.system import (
    GemsComponent,
    GemsComponentConnection,
    GemsSystem,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.integration.conftest import RUN_ON_WINDOWS
from tests.study.dao.conftest import _build_db_dao_unreleased_version, check_gems_system_integrity
from tests.study.dao.utils import save_area

ASSETS_PATH = Path(__file__).parent / "assets"
DATA_SERIES_PATH = ASSETS_PATH / "gems" / "data-series"


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_replace_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    # First, ensure there is no system in the study
    assert dao.get_system() is None
    assert dao.get_components() == []

    system = _add_system_file_to_study_dao(dao)

    # Ensures we cannot replace a system once it already exists in a study
    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_system_is_not_saved_if_an_error_is_raised(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_library_file_to_study_dao(dao)

    # Ensures the system is not saved if an error is raised during the save process
    falsy_component = GemsComponent(id="dsr", model="andromede-v1-models-weo-hybrid.missing_model")
    system = GemsSystem(id="sys_id", components=[falsy_component])

    with pytest.raises(Exception):
        dao.save_system(system)

    assert dao.get_system() is None

    # Fix component and save again
    fixed_component = GemsComponent(id="dsr", model="andromede-v1-models-weo-hybrid.dsr")
    system = GemsSystem(id="sys_id", components=[fixed_component])
    dao.save_system(system)
    assert dao.get_system() is not None


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_save_and_load_system(dao_10_2: StudyDao, matrix_service: ISimpleMatrixService) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)

    # Fetch the saved system and check its content. Time-/scenario-dependent parameter values are
    # now opaque matrix ids (not the data series id used in the source file), so we skip that part
    # of the generic integrity check and verify it separately below.
    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system, matrix_service)

    # `get_components` should return the same components as `get_system`
    components = dao.get_components()
    assert components == saved_system.components

    max_load_parameter = saved_system.components[0].parameters[1]
    assert max_load_parameter.id == "max_load"
    assert isinstance(max_load_parameter.value, str)

    p_max_parameter = saved_system.components[1].parameters[1]
    assert p_max_parameter.id == "p_max"
    assert isinstance(p_max_parameter.value, str)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_save_components_without_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    assert dao.get_system() is None

    new_component = GemsComponent.model_validate({"id": "comp3", "model": "model3"})
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_components([new_component])


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_save_components_fully_replaces_existing_ones(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)

    updated_comp1 = GemsComponent.model_validate(
        {
            "id": "comp1",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {"id": "param4", "time-dependent": False, "scenario-dependent": False, "value": 7.0},
            ],
        }
    )
    new_comp3 = GemsComponent.model_validate(
        {
            "id": "comp3",
            "model": "andromede-v1-models-weo-hybrid.electrolyser",
            "parameters": [
                {"id": "param5", "time-dependent": False, "scenario-dependent": False, "value": 8.0},
            ],
            "properties": [
                {"id": "prop4", "value": "third_component"},
            ],
        }
    )
    dao.save_components([updated_comp1, new_comp3])

    components = dao.get_components()
    assert components is not None
    assert len(components) == 2
    assert {component.id for component in components} == {"comp1", "comp3"}

    first_component = components[0]
    assert first_component.id == "comp1"
    assert first_component.model == "andromede-v1-models-weo-hybrid.dsr"
    assert first_component.scenario_group is None
    assert first_component.parameters is not None
    assert len(first_component.parameters) == 1
    assert first_component.parameters[0].id == "param4"
    assert first_component.parameters[0].value == 7.0
    assert first_component.properties == []

    third_component = components[1]
    assert third_component.id == "comp3"
    assert third_component.model == "andromede-v1-models-weo-hybrid.electrolyser"
    assert third_component.scenario_group is None
    assert third_component.parameters is not None
    assert third_component.parameters[0].id == "param5"
    assert third_component.parameters[0].value == 8.0
    assert third_component.properties is not None
    assert third_component.properties[0].id == "prop4"
    assert third_component.properties[0].value == "third_component"


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_connections_are_optional(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    system = GemsSystem.model_validate({"id": "sys_id", "components": []})
    dao.save_system(system)

    loaded_system = dao.get_system()
    assert loaded_system is not None
    assert loaded_system.connections == []


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_connections_can_link_2_ports_of_the_same_component(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    library = GemsLibrary.model_validate(
        {
            "id": "test_lib_id",
            "models": [
                {
                    "id": "dsr",
                    "properties": [],
                    "parameters": [],
                    "ports": [{"id": "port1", "type": "flow"}, {"id": "port2", "type": "flow"}],
                }
            ],
        }
    )
    dao.save_library(library)

    component = GemsComponent.model_validate({"id": "dsr", "model": "test_lib_id.dsr"})

    self_connection = GemsComponentConnection(component1="dsr", port1="port1", component2="dsr", port2="port2")
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component], "connections": [self_connection]})

    dao.save_system(system)
    assert dao.get_system() is not None


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_have_duplicated_connections(dao_10_2: StudyDao) -> None:

    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    component1 = GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})
    component2 = GemsComponent.model_validate(
        {"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}
    )

    connection = GemsComponentConnection(
        component1="dsr", port1="balance_port", component2="electrolyser", port2="hydrogen_port"
    )
    duplicated_connection = connection.model_copy()

    system = GemsSystem.model_validate(
        {
            "id": "sys_id",
            "components": [component1, component2],
            "connections": [connection, duplicated_connection],
        }
    )

    with pytest.raises(
        GemsInvalidConnection,
        match="Connection between 'dsr.balance_port' and 'electrolyser.hydrogen_port' is declared more than once",
    ):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_symmetric_connections_are_detected_as_identical(dao_10_2: StudyDao) -> None:

    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    component1 = GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})
    component2 = GemsComponent.model_validate(
        {"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}
    )

    connection = GemsComponentConnection(
        component1="dsr", port1="balance_port", component2="electrolyser", port2="hydrogen_port"
    )
    symmetric_connection = GemsComponentConnection(
        component1="electrolyser", port1="hydrogen_port", component2="dsr", port2="balance_port"
    )
    system = GemsSystem.model_validate(
        {
            "id": "sys_id",
            "components": [component1, component2],
            "connections": [connection, symmetric_connection],
        }
    )

    with pytest.raises(
        GemsInvalidConnection,
        match="Connection between 'dsr.balance_port' and 'electrolyser.hydrogen_port' is declared more than once",
    ):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_connections_cannot_link_a_port_of_a_component_to_itself(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    component = GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})

    self_loop_connection = GemsComponentConnection(
        component1="dsr", port1="balance_port", component2="dsr", port2="balance_port"
    )
    system = GemsSystem.model_validate(
        {"id": "sys_id", "components": [component], "connections": [self_loop_connection]}
    )

    with pytest.raises(
        GemsInvalidConnection, match="A connection cannot link the port 'balance_port' of component 'dsr' to itself"
    ):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_connections_must_link_2_existing_components(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    component = GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})

    connection = GemsComponentConnection(
        component1="dsr", port1="hydrogen_port", component2="non_existing_component", port2="hydrogen_port"
    )
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component], "connections": [connection]})

    with pytest.raises(
        GemsInvalidConnection,
        match=re.escape("Connection(s) reference non-existing component(s): ['non_existing_component']"),
    ):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_parameter_value_must_be_a_float_when_value_does_not_depend_on_time_or_scenario(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    # Parameter type mismatches are detected before any file is read, so the referenced data series
    # files do not even need to exist on disk for this test.
    component = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {"id": "param1", "time-dependent": True, "scenario-dependent": False, "value": "demand_profile1"},
                {"id": "param2", "time-dependent": False, "scenario-dependent": True, "value": "demand_profile2"},
                {"id": "param3", "time-dependent": False, "scenario-dependent": False, "value": "demand_profile2"},
                {"id": "param4", "time-dependent": True, "scenario-dependent": False, "value": 42},
                {"id": "param5", "time-dependent": False, "scenario-dependent": True, "value": 3.14},
                {"id": "param6", "time-dependent": True, "scenario-dependent": True, "value": "demand_profile3"},
                {"id": "param7", "time-dependent": True, "scenario-dependent": True, "value": 2.718},
            ],
        }
    )
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component]})

    with pytest.raises(
        GemsInvalidParameterValue,
        match=re.escape(
            "Parameter value(s) must be a float when they do not depend on time or scenario: ['param3']\n"
            + "Parameter value(s) must be a string when they depend on time or scenario: ['param4', 'param5', 'param7']"
        ),
    ):
        dao.save_system(system)

    assert dao.get_system() is None


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_deleting_a_cluster_removes_its_connections(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)
    coal_cluster = ThermalCluster(id="coal_cluster", name="Coal_Cluster")
    initialize_thermal_cluster(coal_cluster, dao.get_version())
    dao.save_thermals({"west": [coal_cluster]})
    dao.save_system(
        GemsSystem.model_validate(
            {
                "id": "sys_id",
                "components": [{"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}],
                "area-connections": [{"component": "electrolyser", "port": "hydrogen_port", "area": "west"}],
                "thermal-capacity-connections": [
                    {
                        "component": "electrolyser",
                        "port": "power_port",
                        "thermal-component": {"area": "west", "cluster-id": "gas_cluster"},
                    },
                    {
                        "component": "electrolyser",
                        "port": "hydrogen_port",
                        "thermal-component": {"area": "west", "cluster-id": "coal_cluster"},
                    },
                ],
            }
        )
    )
    system_before = dao.get_system()
    assert system_before is not None
    assert {c.thermal_component.cluster_id for c in system_before.thermal_capacity_connections} == {
        "gas_cluster",
        "coal_cluster",
    }

    dao.delete_thermal("west", "gas_cluster")

    system = dao.get_system()
    assert system is not None
    # Only the connection to the deleted cluster is removed
    assert {c.thermal_component.cluster_id for c in system.thermal_capacity_connections} == {"coal_cluster"}
    assert system.area_connections == system_before.area_connections


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_deleting_an_area_removes_its_connections_and_the_ones_of_its_clusters(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None
    assert [(c.component, c.port, c.area) for c in system_before.area_connections] == [
        ("electrolyser", "hydrogen_port", "west-h2"),
        ("electrolyser", "power_port", "west"),
    ]
    assert [
        (c.component, c.thermal_component.area, c.thermal_component.cluster_id)
        for c in system_before.thermal_capacity_connections
    ] == [("electrolyser", "west", "gas_cluster")]

    dao.delete_area("west")

    system = dao.get_system()
    assert system is not None
    assert system.thermal_capacity_connections == []
    assert [(c.component, c.port, c.area) for c in system.area_connections] == [
        ("electrolyser", "hydrogen_port", "west-h2")
    ]
    # Components stay in the system
    assert [component.id for component in system.components] == ["dsr", "electrolyser"]


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
@pytest.mark.parametrize(
    "section, connections, error_msg",
    [
        pytest.param(
            "area-connections",
            [{"component": "unknown", "port": "power_port", "area": "west"}],
            "area-connections: component 'unknown' does not exist",
            id="unknown_component",
        ),
        pytest.param(
            "area-connections",
            [{"component": "dsr", "port": "balance_port", "area": "unknown"}],
            "Component 'dsr' is connected to a non-existing area 'unknown'",
            id="unknown_area",
        ),
        pytest.param(
            "thermal-capacity-connections",
            [
                {
                    "component": "dsr",
                    "port": "balance_port",
                    "thermal-component": {"area": "west", "cluster-id": "unknown"},
                }
            ],
            "Component 'dsr' is connected to a non-existing thermal cluster 'unknown' in area 'west'",
            id="unknown_cluster",
        ),
        pytest.param(
            "thermal-capacity-connections",
            [
                {
                    "component": "dsr",
                    "port": "balance_port",
                    "thermal-component": {"area": "unknown", "cluster-id": "gas_cluster"},
                }
            ],
            "Component 'dsr' is connected to a non-existing thermal cluster 'gas_cluster' in area 'unknown'",
            id="unknown_cluster_area",
        ),
        pytest.param(
            "thermal-capacity-connections",
            [
                {
                    "component": "dsr",
                    "port": "balance_port",
                    "thermal-component": {"area": "West", "cluster-id": "Gas_Cluster"},
                }
            ],
            "Component 'dsr' is connected to a non-existing thermal cluster 'Gas_Cluster' in area 'west'",
            id="cluster_id_not_lowercased",
        ),
        pytest.param(
            "area-connections",
            [
                {"component": "dsr", "port": "balance_port", "area": "west"},
                {"component": "dsr", "port": "balance_port", "area": "west-h2"},
            ],
            "area-connections: port 'balance_port' of component 'dsr' is connected more than once",
            id="port_connected_twice",
        ),
    ],
)
def test_cannot_save_invalid_legacy_connections(
    dao_10_2: StudyDao, section: str, connections: list[dict[str, Any]], error_msg: str
) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)

    system = GemsSystem.model_validate(
        {
            "id": "sys_id",
            "components": [{"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"}],
            section: connections,
        }
    )

    with pytest.raises(GemsInvalidConnection, match=error_msg):
        dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["fs"], indirect=True)
def test_cannot_delete_legacy_objects_connected_to_gems_in_filesystem_studies(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    system = _add_system_file_to_study_dao(dao)

    with pytest.raises(
        GemsConnectedObjectDeletionNotAllowed,
        match="Cluster 'gas_cluster' is not allowed to be deleted, because the following GEMS components"
        " are connected to it: 'electrolyser'",
    ):
        dao.delete_thermal("west", "gas_cluster")
    with pytest.raises(
        GemsConnectedObjectDeletionNotAllowed,
        match="Area 'west-h2' is not allowed to be deleted, because the following GEMS components"
        " are connected to it: 'electrolyser'",
    ):
        dao.delete_area("west-h2")

    # Nothing has been deleted
    assert set(dao.get_all_area_ids()) >= {"west", "west-h2"}
    assert "gas_cluster" in dao.get_all_thermals()["west"]
    assert dao.get_system() == system

    # Legacy objects that are not connected to GEMS components can still be deleted
    save_area(dao, "east")
    dao.delete_area("east")
    assert "east" not in dao.get_all_area_ids()


@pytest.mark.parametrize("dao_10_2", ["fs"], indirect=True)
def test_cannot_delete_area_whose_clusters_are_connected_to_gems_in_filesystem_studies(
    dao_10_2: StudyDao,
) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)
    # The area is only referenced through its thermal cluster
    system = GemsSystem.model_validate(
        {
            "id": "sys_id",
            "components": [{"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}],
            "thermal-capacity-connections": [
                {
                    "component": "electrolyser",
                    "port": "power_port",
                    "thermal-component": {"area": "west", "cluster-id": "gas_cluster"},
                }
            ],
        }
    )
    dao.save_system(system)

    with pytest.raises(
        GemsConnectedObjectDeletionNotAllowed,
        match="Area 'west' is not allowed to be deleted, because the following GEMS components"
        " are connected to it: 'electrolyser'",
    ):
        dao.delete_area("west")

    # Nothing has been deleted
    assert "west" in dao.get_all_area_ids()
    assert dao.get_system() == system


def _add_legacy_objects_to_study_dao(dao: StudyDao) -> None:
    # Legacy objects referenced by the system file asset
    save_area(dao, "west")
    save_area(dao, "West-H2")
    cluster = ThermalCluster(id="gas_cluster", name="Gas_Cluster")
    initialize_thermal_cluster(cluster, dao.get_version())
    dao.save_thermals({"west": [cluster]})


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_parameter_value_can_reference_an_existing_data_series(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    data_series_path = DATA_SERIES_PATH / "max_load_values.csv"
    component = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {"id": "param1", "time-dependent": True, "scenario-dependent": False, "value": str(data_series_path)},
            ],
        }
    )
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component]})
    dao.save_system(system)

    components = dao.get_components()
    assert components[0].parameters is not None
    # The stored value is now the matrix id, not the file path nor its content.
    matrix_id = components[0].parameters[0].value
    assert isinstance(matrix_id, str)
    assert matrix_id != str(data_series_path)

    expected_values = np.loadtxt(data_series_path, delimiter=",", ndmin=2)
    assert np.array_equal(dao.get_parameter_value("dsr", "param1"), expected_values)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_parameter_value_referencing_a_missing_file_is_rejected(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_library_file_to_study_dao(dao)

    missing_path = DATA_SERIES_PATH / "this_file_does_not_exist.csv"
    component = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {"id": "param1", "time-dependent": True, "scenario-dependent": False, "value": str(missing_path)},
                {"id": "param2", "time-dependent": False, "scenario-dependent": False, "value": 2.0},
            ],
        }
    )
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component]})

    with pytest.raises(
        GemsInvalidParameterValue,
        match=re.escape(f"Parameter value(s) reference a missing file: 'dsr.param1' -> '{missing_path}'"),
    ):
        dao.save_system(system)

    assert dao.get_system() is None


@pytest.mark.skipif(RUN_ON_WINDOWS, reason="Docker fails on Windows")
def test_parameter_value_referencing_a_missing_file_is_rejected_on_postgresql() -> None:
    # This check is purely file-system based and runs before any DB statement is issued, so unlike
    # a DB-level referential integrity check, it cannot leave a PostgreSQL transaction in an aborted
    # state: there is nothing to roll back from.
    with PostgresContainer("postgres:14") as postgres:
        engine = create_engine(postgres.get_connection_url())
        Base.metadata.create_all(engine)
        matrix_service = InMemorySimpleMatrixService()

        with contextlib.closing(sessionmaker(bind=engine)()) as db_session:
            dao = _build_db_dao_unreleased_version(db_session, matrix_service, STUDY_VERSION_10_2)

            _add_library_file_to_study_dao(dao)

            missing_path = DATA_SERIES_PATH / "this_file_does_not_exist.csv"
            component = GemsComponent.model_validate(
                {
                    "id": "dsr",
                    "model": "andromede-v1-models-weo-hybrid.dsr",
                    "parameters": [
                        {
                            "id": "param1",
                            "time-dependent": True,
                            "scenario-dependent": False,
                            "value": str(missing_path),
                        },
                    ],
                }
            )
            system = GemsSystem.model_validate({"id": "sys_id", "components": [component]})

            with pytest.raises(
                GemsInvalidParameterValue,
                match=re.escape(f"Parameter value(s) reference a missing file: 'dsr.param1' -> '{missing_path}'"),
            ):
                dao.save_system(system)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_matrices_are_isolated_between_studies(dao_10_2: StudyDao, db_dao: DatabaseStudyDao) -> None:
    # `dao_10_2` and `db_dao` point to two distinct studies sharing the same matrix store.
    first_component = _create_component_with_data_series_path("dsr", "param1", DATA_SERIES_PATH / "max_load_values.csv")
    second_component = _create_component_with_data_series_path(
        "dsr", "param1", DATA_SERIES_PATH / "time-and-scenario-dependent-example.csv"
    )

    _add_library_file_to_study_dao(dao_10_2)
    dao_10_2.save_system(GemsSystem.model_validate({"id": "sys_id", "components": [first_component]}))

    _add_library_file_to_study_dao(db_dao)
    db_dao.save_system(GemsSystem.model_validate({"id": "sys_id", "components": [second_component]}))

    first_expected = np.loadtxt(DATA_SERIES_PATH / "max_load_values.csv", delimiter=",", ndmin=2)
    second_expected = np.loadtxt(DATA_SERIES_PATH / "time-and-scenario-dependent-example.csv", delimiter=",", ndmin=2)

    assert np.array_equal(dao_10_2.get_parameter_value("dsr", "param1"), first_expected)
    assert np.array_equal(db_dao.get_parameter_value("dsr", "param1"), second_expected)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_get_parameter_value_raises_when_component_or_parameter_not_found(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)

    with pytest.raises(GemsParameterNotFound, match="Parameter 'unknown' not found for component 'dsr'"):
        dao.get_parameter_value("dsr", "unknown")

    with pytest.raises(GemsParameterNotFound, match="Parameter 'max_load' not found for component 'unknown'"):
        dao.get_parameter_value("unknown", "max_load")


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_get_parameter_value_raises_when_parameter_is_a_constant(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)

    with pytest.raises(
        GemsInvalidParameterValue,
        match="Parameter 'curtailment_price' of component 'dsr' is a constant, it does not reference a matrix",
    ):
        dao.get_parameter_value("dsr", "curtailment_price")


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_save_components_uploads_matrices_in_a_single_batch(dao_10_2: StudyDao, db_dao: DatabaseStudyDao) -> None:
    _add_library_file_to_study_dao(dao_10_2)

    component = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {
                    "id": "param1",
                    "time-dependent": True,
                    "scenario-dependent": False,
                    "value": str(DATA_SERIES_PATH / "max_load_values.csv"),
                },
                {
                    "id": "param2",
                    "time-dependent": True,
                    "scenario-dependent": True,
                    "value": str(DATA_SERIES_PATH / "time-and-scenario-dependent-example.csv"),
                },
            ],
        }
    )
    system = GemsSystem.model_validate({"id": "sys_id", "components": [component]})

    # `dao_10_2` and `db_dao` share the same underlying matrix service instance.
    matrix_service = db_dao.matrix_service
    with patch.object(matrix_service, "create_batch", wraps=matrix_service.create_batch) as create_batch_spy:
        dao_10_2.save_system(system)

    create_batch_spy.assert_called_once()


def _add_system_file_to_study_dao(dao: StudyDao) -> GemsSystem:
    # Add the library and the legacy objects first, as the system file requires them
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)
    dao.save_gems_scenario_builder(
        GemsScenarioBuilder(scenarios={"sg1": [GemsScBuilderMapping(scenario=0, time_series_index=1)]})
    )

    gems_system_asset_path = ASSETS_PATH / "gems" / "system" / "system.yml"
    content = YAMLReader().read(gems_system_asset_path)["system"]
    system = GemsSystem.model_validate(content)

    # The system file references dependent parameters by data series id, matching the real-world
    # file-based `system.yml` convention. `save_components` reads the matrix from an actual file, so
    # we resolve those ids to the matching CSV asset before saving.
    for component in system.components:
        for parameter in component.parameters:
            if parameter.time_dependent or parameter.scenario_dependent:
                parameter.value = str(DATA_SERIES_PATH / f"{parameter.value}.csv")

    dao.save_system(system)
    return system


def _add_library_file_to_study_dao(dao: StudyDao) -> None:
    gems_library_asset_path = ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml"
    content = YAMLReader().read(gems_library_asset_path)["library"]
    library = GemsLibrary.model_validate(content)
    dao.save_library(library)


def _create_component_with_data_series_path(component_id: str, parameter_id: str, csv_path: Path) -> GemsComponent:
    return GemsComponent.model_validate(
        {
            "id": component_id,
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {"id": parameter_id, "time-dependent": True, "scenario-dependent": False, "value": str(csv_path)},
            ],
        }
    )
