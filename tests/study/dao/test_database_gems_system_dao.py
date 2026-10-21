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
    GemsComponentNotFound,
    GemsConnectedObjectDeletionNotAllowed,
    GemsConnectionNotFound,
    GemsInvalidComponent,
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
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_gems_system_integrity
from tests.study.dao.utils import save_area

ASSETS_PATH = Path(__file__).parent / "assets"


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
def test_save_and_load_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)

    # Fetch the saved system and check its content
    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system)

    # `get_components` should return the same components as `get_system`
    components = dao.get_components()
    assert components == saved_system.components


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_save_or_delete_components_without_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    assert dao.get_system() is None

    new_component = GemsComponent.model_validate({"id": "comp3", "model": "model3"})
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_components([new_component])

    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.delete_components(["comp3"])


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_save_components_adds_new_ones_and_updates_existing_ones(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None

    updated_dsr = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "scenario-group": "sg1",
            "parameters": [
                {"id": "max_load", "time-dependent": False, "scenario-dependent": False, "value": 500.0},
            ],
            "properties": [
                {"id": "prop1", "value": "updated_component"},
            ],
        }
    )
    new_electrolyser = GemsComponent.model_validate(
        {
            "id": "electrolyser2",
            "model": "andromede-v1-models-weo-hybrid.electrolyser",
            "parameters": [
                {"id": "p_max", "time-dependent": False, "scenario-dependent": False, "value": 100.0},
            ],
        }
    )
    dao.save_components([updated_dsr, new_electrolyser])

    # The parameters of `dsr` are replaced, and the other components are left untouched
    components = {component.id: component for component in dao.get_components()}
    assert components == {
        "dsr": updated_dsr,
        "electrolyser": system_before.components[1],
        "electrolyser2": new_electrolyser,
    }

    # The connections of the updated components are kept
    system = dao.get_system()
    assert system is not None
    assert system.connections == system_before.connections
    assert system.area_connections == system_before.area_connections
    assert system.thermal_capacity_connections == system_before.thermal_capacity_connections


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_save_duplicated_components(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()

    component = GemsComponent.model_validate({"id": "dsr", "model": "andromede-v1-models-weo-hybrid.dsr"})
    with pytest.raises(GemsInvalidComponent, match="Component 'dsr' is declared more than once"):
        dao.save_components([component, component])

    # Nothing has been saved
    assert dao.get_system() == system_before


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_delete_components_removes_them_with_their_connections(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)

    dao.delete_components(["electrolyser"])

    system = dao.get_system()
    assert system is not None
    assert [component.id for component in system.components] == ["dsr"]
    assert system.connections == []
    assert system.area_connections == []
    assert system.thermal_capacity_connections == []


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_delete_non_existing_components(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()

    with pytest.raises(GemsComponentNotFound, match=re.escape("Component(s) not found in the system: ['unknown']")):
        dao.delete_components(["dsr", "unknown"])

    # Nothing has been deleted
    assert dao.get_system() == system_before


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
def test_save_connections_adds_them_to_the_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None

    new_connection = GemsComponentConnection(
        component1="electrolyser", port1="power_port", component2="dsr", port2="balance_port"
    )
    # A connection already in the system, whatever the order of its endpoints, is left untouched
    symmetric_connection = GemsComponentConnection(
        component1="electrolyser", port1="hydrogen_port", component2="dsr", port2="balance_port"
    )
    dao.save_connections([new_connection, symmetric_connection])

    system = dao.get_system()
    assert system is not None
    assert system.connections == [*system_before.connections, new_connection]
    # The rest of the system is untouched
    assert system.components == system_before.components
    assert system.area_connections == system_before.area_connections


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_delete_connections_whatever_the_order_of_their_endpoints(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None

    # The connection is stored as 'dsr.balance_port' -> 'electrolyser.hydrogen_port'
    symmetric_connection = GemsComponentConnection(
        component1="electrolyser", port1="hydrogen_port", component2="dsr", port2="balance_port"
    )
    dao.delete_connections([symmetric_connection])

    system = dao.get_system()
    assert system is not None
    assert system.connections == []
    # The rest of the system is untouched
    assert system.components == system_before.components
    assert system.area_connections == system_before.area_connections


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_delete_non_existing_connections(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None

    unknown_connection = GemsComponentConnection(
        component1="electrolyser", port1="power_port", component2="dsr", port2="balance_port"
    )
    with pytest.raises(
        GemsConnectionNotFound,
        match="Connection between 'electrolyser.power_port' and 'dsr.balance_port' does not exist",
    ):
        dao.delete_connections([*system_before.connections, unknown_connection])

    # Nothing has been deleted
    assert dao.get_system() == system_before


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_save_or_delete_connections_without_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    connection = GemsComponentConnection(
        component1="dsr", port1="balance_port", component2="electrolyser", port2="hydrogen_port"
    )
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_connections([connection])

    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.delete_connections([connection])


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_deleting_a_cluster_removes_its_connections(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)

    dao.delete_thermal("west", "gas_cluster")

    system = dao.get_system()
    assert system is not None
    assert system.thermal_capacity_connections == []
    assert len(system.area_connections) == 2


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_deleting_an_area_removes_its_connections_and_the_ones_of_its_clusters(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)

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
def test_save_legacy_connections_adds_them_to_the_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
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


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_save_legacy_connections_reconnects_already_connected_ports(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None
    coal_cluster = ThermalCluster(id="coal_cluster", name="Coal_Cluster")
    initialize_thermal_cluster(coal_cluster, dao.get_version())
    dao.save_thermals({"west-h2": [coal_cluster]})

    # 'electrolyser.hydrogen_port' was connected to the area 'west-h2'
    area_connection = GemsAreaConnection(component="electrolyser", port="hydrogen_port", area="west")
    dao.save_area_connections([area_connection])
    # 'electrolyser.power_port' was connected to the cluster 'gas_cluster' of the area 'west'
    thermal_connection = GemsThermalCapacityConnection.model_validate(
        {
            "component": "electrolyser",
            "port": "power_port",
            "thermal-component": {"area": "west-h2", "cluster-id": "coal_cluster"},
        }
    )
    dao.save_thermal_capacity_connections([thermal_connection])

    system = dao.get_system()
    assert system is not None
    assert system.area_connections == [area_connection, system_before.area_connections[1]]
    assert system.thermal_capacity_connections == [thermal_connection]


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_delete_legacy_connections_removes_them_from_the_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()
    assert system_before is not None

    # The area is lowercased, as Antares Simulator does
    dao.delete_area_connections([GemsAreaConnection(component="electrolyser", port="hydrogen_port", area="West-H2")])
    dao.delete_thermal_capacity_connections(system_before.thermal_capacity_connections)

    system = dao.get_system()
    assert system is not None
    assert system.area_connections == [system_before.area_connections[1]]
    assert system.thermal_capacity_connections == []
    # The rest of the system is untouched
    assert system.components == system_before.components
    assert system.connections == system_before.connections


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_save_or_delete_legacy_connections_without_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    area_connection = GemsAreaConnection(component="electrolyser", port="power_port", area="west")
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_area_connections([area_connection])
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.delete_area_connections([area_connection])

    thermal_connection = GemsThermalCapacityConnection.model_validate(
        {
            "component": "electrolyser",
            "port": "power_port",
            "thermal-component": {"area": "west", "cluster-id": "gas_cluster"},
        }
    )
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.save_thermal_capacity_connections([thermal_connection])
    with pytest.raises(GemsSystemNotFound, match="No system configuration found for study"):
        dao.delete_thermal_capacity_connections([thermal_connection])


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
                    "thermal-component": {"area": "West", "cluster-id": "Gas_Cluster"},
                }
            ],
            # Antares Simulator matches the cluster id exactly, only the area is lowercased
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
    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()

    with pytest.raises(GemsInvalidConnection, match=error_msg):
        if section == "area-connections":
            dao.save_area_connections([GemsAreaConnection.model_validate(c) for c in connections])
        else:
            dao.save_thermal_capacity_connections(
                [GemsThermalCapacityConnection.model_validate(c) for c in connections]
            )

    # Nothing has been saved
    assert dao.get_system() == system_before


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
@pytest.mark.parametrize(
    "section, connections, error_msg",
    [
        pytest.param(
            "area-connections",
            [
                {"component": "electrolyser", "port": "power_port", "area": "west"},
                {"component": "electrolyser", "port": "hydrogen_port", "area": "west"},
            ],
            "area-connections: port 'hydrogen_port' of component 'electrolyser' is not connected to area 'west'",
            id="area_connection",
        ),
        pytest.param(
            "thermal-capacity-connections",
            [
                {
                    "component": "electrolyser",
                    "port": "power_port",
                    "thermal-component": {"area": "west", "cluster-id": "unknown"},
                }
            ],
            "thermal-capacity-connections: port 'power_port' of component 'electrolyser' is not connected"
            " to thermal cluster 'unknown' in area 'west'",
            id="thermal_capacity_connection",
        ),
    ],
)
def test_cannot_delete_non_existing_legacy_connections(
    dao_10_2: StudyDao, section: str, connections: list[dict[str, Any]], error_msg: str
) -> None:
    dao = dao_10_2
    _add_system_file_to_study_dao(dao)
    system_before = dao.get_system()

    with pytest.raises(GemsConnectionNotFound, match=error_msg):
        if section == "area-connections":
            dao.delete_area_connections([GemsAreaConnection.model_validate(c) for c in connections])
        else:
            dao.delete_thermal_capacity_connections(
                [GemsThermalCapacityConnection.model_validate(c) for c in connections]
            )

    # Nothing has been deleted
    assert dao.get_system() == system_before


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


def _add_library_file_to_study_dao(dao: StudyDao) -> None:
    gems_library_asset_path = ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml"
    content = YAMLReader().read(gems_library_asset_path)["library"]
    library = GemsLibrary.model_validate(content)
    dao.save_library(library)
