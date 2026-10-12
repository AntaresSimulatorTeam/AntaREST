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
import re
from pathlib import Path
from typing import Any

import pytest

from antarest.core.exceptions import (
    GemsConnectedObjectDeletionNotAllowed,
    GemsInvalidConnection,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.business.model.gems.system import (
    GemsAreaConnection,
    GemsComponent,
    GemsComponentConnection,
    GemsSystem,
    GemsThermalCapacityConnection,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_gems_system_integrity
from tests.study.dao.utils import save_area

ASSETS_PATH = Path(__file__).parent / "assets"


def test_cannot_replace_system(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

    # First, ensure there is no system in the study
    assert dao.get_system() is None
    assert dao.get_components() == []

    system = _add_system_file_to_study_dao(dao)

    # Ensures we cannot replace a system once it already exists in a study
    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


def test_system_is_not_saved_if_an_error_is_raised(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

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


def test_save_and_load_system(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

    _add_system_file_to_study_dao(dao)

    # Fetch the saved system and check its content
    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system)

    # `get_components` should return the same components as `get_system`
    components = dao.get_components()
    assert components == saved_system.components


def test_cannot_save_components_without_system(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

    assert dao.get_system() is None

    new_component = GemsComponent.model_validate({"id": "comp3", "model": "model3"})
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_components([new_component])


def test_save_components_fully_replaces_existing_ones(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

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
    assert first_component.properties is None

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


def test_connections_are_optional(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_library_file_to_study_dao(dao)

    system = GemsSystem.model_validate({"id": "sys_id", "components": []})
    dao.save_system(system)

    loaded_system = dao.get_system()
    assert loaded_system is not None
    assert loaded_system.connections == []


def test_connections_can_link_2_ports_of_the_same_component(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

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


def test_cannot_have_duplicated_connections(db_dao_10_2: DatabaseStudyDao) -> None:

    dao = db_dao_10_2
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


def test_symmetric_connections_are_detected_as_identical(db_dao_10_2: DatabaseStudyDao) -> None:

    dao = db_dao_10_2
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


def test_connections_cannot_link_a_port_of_a_component_to_itself(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
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


def test_connections_must_link_2_existing_components(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
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


def test_legacy_connections_are_optional(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_library_file_to_study_dao(dao)

    dao.save_system(GemsSystem.model_validate({"id": "sys_id", "components": []}))

    system = dao.get_system()
    assert system is not None
    assert system.area_connections is None
    assert system.thermal_capacity_connections is None
    # Absent sections must not be written back to a system file
    assert system.model_dump(by_alias=True, exclude_unset=True) == {
        "id": "sys_id",
        "description": None,
        "components": [],
        "connections": [],
    }


@pytest.mark.parametrize(
    "section, connection, error_msg",
    [
        pytest.param(
            "area-connections",
            {"component": "electrolyser", "port": "power_port", "area": "unknown"},
            "Component 'electrolyser' is connected to a non-existing area 'unknown'",
            id="unknown_area",
        ),
        pytest.param(
            "thermal-capacity-connections",
            {
                "component": "electrolyser",
                "port": "power_port",
                "thermal-component": {"area": "west", "cluster-id": "unknown"},
            },
            "Component 'electrolyser' is connected to a non-existing thermal cluster 'unknown' in area 'west'",
            id="unknown_cluster",
        ),
    ],
)
def test_cannot_save_system_with_invalid_legacy_connection(
    db_dao_10_2: DatabaseStudyDao, section: str, connection: dict[str, Any], error_msg: str
) -> None:
    dao = db_dao_10_2
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)

    system = GemsSystem.model_validate(
        {
            "id": "sys_id",
            "components": [{"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}],
            section: [connection],
        }
    )
    with pytest.raises(GemsInvalidConnection, match=error_msg):
        dao.save_system(system)


def test_save_components_keeps_legacy_connections_of_remaining_components(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    system = _add_system_file_to_study_dao(dao)

    # Saving the same components keeps all their legacy connections
    dao.save_components(system.components)
    saved_system = dao.get_system()
    assert saved_system is not None
    assert saved_system.area_connections == system.area_connections
    assert saved_system.thermal_capacity_connections == system.thermal_capacity_connections

    # The connections of a component are removed with it
    dao.save_components([GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})])
    saved_system = dao.get_system()
    assert saved_system is not None
    assert saved_system.area_connections is None
    assert saved_system.thermal_capacity_connections is None


def test_deleting_legacy_objects_removes_their_connections(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_system_file_to_study_dao(dao)

    # Deleting a thermal cluster removes its thermal capacity connection
    dao.delete_thermal("west", "gas_cluster")
    system = dao.get_system()
    assert system is not None
    assert system.thermal_capacity_connections is None
    assert system.area_connections is not None
    assert len(system.area_connections) == 2

    # Deleting an area removes its area connections
    dao.delete_area("west-h2")
    system = dao.get_system()
    assert system is not None
    assert system.area_connections is not None
    assert [(c.component, c.port, c.area) for c in system.area_connections] == [("electrolyser", "power_port", "west")]

    dao.delete_area("west")
    system = dao.get_system()
    assert system is not None
    assert system.area_connections is None

    # Components stay in the system
    assert [component.id for component in system.components] == ["dsr", "electrolyser"]


def test_deleting_an_area_removes_the_connections_to_its_thermal_clusters(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_system_file_to_study_dao(dao)

    dao.delete_area("west")

    system = dao.get_system()
    assert system is not None
    assert system.thermal_capacity_connections is None
    assert system.area_connections is not None
    assert [(c.component, c.port, c.area) for c in system.area_connections] == [
        ("electrolyser", "hydrogen_port", "west-h2")
    ]


def test_save_legacy_connections_adds_them_to_the_system(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_library_file_to_study_dao(dao)
    _add_legacy_objects_to_study_dao(dao)
    dao.save_system(
        GemsSystem.model_validate(
            {
                "id": "sys_id",
                "components": [{"id": "electrolyser", "model": "andromede-v1-models-weo-hybrid.electrolyser"}],
            }
        )
    )

    area_connection = GemsAreaConnection(component="electrolyser", port="power_port", area="West-H2")
    dao.save_area_connections([area_connection])
    thermal_connection = GemsThermalCapacityConnection.model_validate(
        {
            "component": "electrolyser",
            "port": "hydrogen_port",
            "thermal-component": {"area": "west", "cluster-id": "gas_cluster"},
        }
    )
    dao.save_thermal_capacity_connections([thermal_connection])

    system = dao.get_system()
    assert system is not None
    assert system.area_connections == [area_connection]
    assert system.thermal_capacity_connections == [thermal_connection]
    # The rest of the system is untouched
    assert [component.id for component in system.components] == ["electrolyser"]


def test_cannot_save_legacy_connections_without_system(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2

    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_area_connections([])
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_thermal_capacity_connections([])


def test_cannot_save_legacy_connections_of_unknown_component(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    system = _add_system_file_to_study_dao(dao)

    with pytest.raises(GemsInvalidConnection, match="area-connections: component 'unknown' does not exist"):
        dao.save_area_connections([GemsAreaConnection(component="unknown", port="power_port", area="west")])

    # Nothing has been saved
    saved_system = dao.get_system()
    assert saved_system is not None
    assert saved_system.area_connections == system.area_connections


def test_cannot_save_legacy_connections_to_unknown_legacy_objects(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    _add_system_file_to_study_dao(dao)

    with pytest.raises(GemsInvalidConnection, match="connected to a non-existing area 'unknown'"):
        dao.save_area_connections([GemsAreaConnection(component="dsr", port="balance_port", area="unknown")])

    thermal_connection = GemsThermalCapacityConnection.model_validate(
        {
            "component": "dsr",
            "port": "balance_port",
            "thermal-component": {"area": "west", "cluster-id": "unknown"},
        }
    )
    with pytest.raises(GemsInvalidConnection, match="non-existing thermal cluster 'unknown' in area 'west'"):
        dao.save_thermal_capacity_connections([thermal_connection])


def test_cannot_save_legacy_connections_on_an_already_connected_port(db_dao_10_2: DatabaseStudyDao) -> None:
    dao = db_dao_10_2
    system = _add_system_file_to_study_dao(dao)

    with pytest.raises(
        GemsInvalidConnection,
        match="area-connections: port 'power_port' of component 'electrolyser' is already connected",
    ):
        dao.save_area_connections([GemsAreaConnection(component="electrolyser", port="power_port", area="west-h2")])

    thermal_connection = GemsThermalCapacityConnection.model_validate(
        {
            "component": "electrolyser",
            "port": "power_port",
            "thermal-component": {"area": "west", "cluster-id": "gas_cluster"},
        }
    )
    with pytest.raises(
        GemsInvalidConnection,
        match="thermal-capacity-connections: port 'power_port' of component 'electrolyser' is already connected",
    ):
        dao.save_thermal_capacity_connections([thermal_connection])

    # Nothing has been saved
    saved_system = dao.get_system()
    assert saved_system is not None
    assert saved_system.area_connections == system.area_connections
    assert saved_system.thermal_capacity_connections == system.thermal_capacity_connections


def test_cannot_delete_legacy_objects_connected_to_gems_in_filesystem_studies(fs_dao_10_2: StudyDao) -> None:
    dao = fs_dao_10_2
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


def _add_library_file_to_study_dao(dao: StudyDao) -> None:
    gems_library_asset_path = ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml"
    library_content = YAMLReader().read(gems_library_asset_path)["library"]
    dao.save_library(GemsLibrary.model_validate(library_content))


def _add_legacy_objects_to_study_dao(dao: StudyDao) -> None:
    # Legacy objects referenced by the system file asset
    save_area(dao, "west")
    save_area(dao, "West-H2")
    cluster = ThermalCluster(id="gas_cluster", name="Gas_Cluster")
    initialize_thermal_cluster(cluster, dao.get_version())
    dao.save_thermals({"west": [cluster]})


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
    dao.save_system(system)
    return system
