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

from antarest.core.exceptions import GemsSystemAlreadyExists, GemsSystemNotFound
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_gems_system_integrity

ASSETS_PATH = Path(__file__).parent / "assets"


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_cannot_replace_system(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    # First, ensure there is no system in the study
    assert dao.get_system() is None
    assert dao.get_components() is None

    system = _add_system_file_to_study_dao(dao)

    # Ensures we cannot replace a system once it already exists in a study
    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


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
            "model": "model1",
            "parameters": [
                {"id": "param4", "time-dependent": False, "scenario-dependent": False, "value": 7.0},
            ],
        }
    )
    new_comp3 = GemsComponent.model_validate(
        {
            "id": "comp3",
            "model": "model3",
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
    assert first_component.model == "model1"
    assert first_component.scenario_group is None
    assert first_component.parameters is not None
    assert len(first_component.parameters) == 1
    assert first_component.parameters[0].id == "param4"
    assert first_component.parameters[0].value == 7.0
    assert first_component.properties is None

    third_component = components[1]
    assert third_component.id == "comp3"
    assert third_component.model == "model3"
    assert third_component.scenario_group is None
    assert third_component.parameters is not None
    assert third_component.parameters[0].id == "param5"
    assert third_component.parameters[0].value == 8.0
    assert third_component.properties is not None
    assert third_component.properties[0].id == "prop4"
    assert third_component.properties[0].value == "third_component"


def _add_system_file_to_study_dao(dao: StudyDao) -> GemsSystem:
    gems_system_asset_path = ASSETS_PATH / "gems" / "system" / "system.yml"
    content = YAMLReader().read(gems_system_asset_path)["system"]
    system = GemsSystem.model_validate(content)
    dao.save_system(system)
    return system
