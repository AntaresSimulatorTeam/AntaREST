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
import shutil
from pathlib import Path

import pytest

from antarest.core.exceptions import GemsSystemAlreadyExists, GemsSystemNotFound
from antarest.study.business.model.gems.system import GemsComponent
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.conftest import check_gems_system_integrity

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # We should not have a system for default studies
    assert filestudy_dao_v10_2.get_system() is None
    assert filestudy_dao_v10_2.get_components() is None


def test_cannot_replace_system(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    input_folder = dao.get_file_study().config.study_path / "input"

    shutil.copy(ASSETS_PATH / "gems" / "system" / "system.yml", input_folder / "system.yml")

    system = dao.get_system()
    assert system is not None

    with pytest.raises(GemsSystemAlreadyExists, match="A system file already exists for study"):
        dao.save_system(system)


def test_cannot_save_components_without_system(filestudy_dao_v10_2: FileStudyTreeDao) -> None:

    assert filestudy_dao_v10_2.get_system() is None

    new_component = GemsComponent.model_validate({"id": "comp3", "model": "model3"})
    with pytest.raises(GemsSystemNotFound, match="No system file exists yet for study"):
        filestudy_dao_v10_2.save_components([new_component])


def test_system_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    input_folder = dao.get_file_study().config.study_path / "input"

    shutil.copy(ASSETS_PATH / "gems" / "system" / "system.yml", input_folder / "system.yml")

    system = dao.get_system()
    assert system is not None
    check_gems_system_integrity(system)

    # `get_components` should return the same components as `get_system`
    components = dao.get_components()
    assert components == system.components

    # Remove the system file
    (input_folder / "system.yml").unlink()
    assert dao.get_system() is None
    assert dao.get_components() is None

    # Save the old content back
    dao.save_system(system)
    saved_system = dao.get_system()
    assert saved_system is not None
    check_gems_system_integrity(saved_system)


def test_save_components_appends_to_existing_ones(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    input_folder = dao.get_file_study().config.study_path / "input"
    shutil.copy(ASSETS_PATH / "gems" / "system" / "system.yml", input_folder / "system.yml")

    new_component = GemsComponent.model_validate(
        {
            "id": "comp3",
            "model": "model3",
            "parameters": [
                {"id": "param4", "time_dependent": False, "scenario_dependent": False, "value": 7.0},
            ],
            "properties": [
                {"id": "prop4", "value": "third_component"},
            ],
        }
    )
    dao.save_components([new_component])

    components = dao.get_components()
    assert components is not None
    assert len(components) == 3
    third_component = components[2]
    assert third_component.id == "comp3"
    assert third_component.model == "model3"
    assert third_component.scenario_group is None
    assert third_component.parameters is not None
    assert third_component.parameters[0].id == "param4"
    assert third_component.parameters[0].value == 7.0
    assert third_component.properties is not None
    assert third_component.properties[0].id == "prop4"
    assert third_component.properties[0].value == "third_component"

    # Original components should be untouched, and the system metadata should be preserved
    assert components[0].id == "comp1"
    assert components[1].id == "comp2"
    system = dao.get_system()
    assert system is not None
    assert system.id == "my_system"
    assert system.description == "A test GEMS system"
