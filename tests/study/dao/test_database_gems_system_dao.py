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

import pytest

from antarest.core.exceptions import (
    GemsInvalidConnection,
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
)
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.business.model.gems.system import GemsComponent, GemsComponentConnection, GemsSystem
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_gems_system_integrity

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

    with pytest.raises(GemsInvalidConnection):
        dao.save_system(system)


def _add_system_file_to_study_dao(dao: StudyDao) -> GemsSystem:
    # Add the library first, as the system file requires it
    _add_library_file_to_study_dao(dao)

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
