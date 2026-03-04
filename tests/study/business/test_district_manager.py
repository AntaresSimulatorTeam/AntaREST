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
from typing import Any
from unittest.mock import patch

import pytest
from helpers import file_study_interface

from antarest.core.exceptions import AreaNotFound, DistrictAlreadyExist, DistrictNotFound
from antarest.study.business.district_manager import DistrictManager
from antarest.study.business.model.district_model import District, DistrictCreation, DistrictDTO, DistrictUpdate
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _check_add_commands(patched_func: Any, expected_cls: Any) -> None:
    assert patched_func.call_count == 1
    commands = patched_func.mock_calls[0].args[0]
    command = commands[0]
    assert isinstance(command, expected_cls)


@pytest.fixture
def manager(command_context: CommandContext) -> DistrictManager:
    return DistrictManager(command_context)


@pytest.fixture
def study_with_sets(empty_study_880: FileStudy) -> FileStudyInterface:
    def dummy_area(name: str) -> AreaConfig:
        return AreaConfig(
            name=name,
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
            st_storages=[],
            st_storages_additional_constraints={},
        )

    district_ini_content = {
        "input": {
            "areas": {
                "list": ["n1", "n2", "n3"],
                "sets": {
                    "d1": {"caption": "D1", "apply-filter": "remove-all", "output": True, "comments": "dummy"},
                    "d2": {
                        "caption": "D2",
                        "apply-filter": "remove-all",
                        "output": True,
                        "comments": "dummy",
                        "+": ["n1", "n2"],
                    },
                    "d3": {
                        "caption": "D2",
                        "apply-filter": "remove-all",
                        "output": False,
                        "comments": "dummy",
                        "+": ["n1", "n2", "n3"],
                    },
                },
            }
        }
    }
    study = file_study_interface(empty_study_880)
    study.file_study.tree.save(district_ini_content)
    study.file_study.config.districts = {
        "d1": District(id="d1", name="D1", add_areas=[], output=True),
        "d2": District(id="d2", name="D2", add_areas=["n1", "n2"], output=True),
        "d3": District(id="d3", name="D2", add_areas=["n1", "n2", "n3"], output=False),
    }
    study.file_study.config.areas = {"n1": dummy_area("n1"), "n2": dummy_area("n2"), "n3": dummy_area("n3")}
    return study


class TestDistrictManager:
    def test_get_districts(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        actual = manager.get_districts(study_with_sets)
        expected = [
            DistrictDTO(
                id="d1",
                name="D1",
                areas=[],
                output=True,
                comments="dummy",
            ),
            DistrictDTO(
                id="d2",
                name="D2",
                areas=["n1", "n2"],
                output=True,
                comments="dummy",
            ),
            DistrictDTO(
                id="d3",
                name="D2",
                areas=["n1", "n2", "n3"],
                output=False,
                comments="dummy",
            ),
        ]
        assert actual == expected

    def test_create_district__district_already_exist(
        self, manager: DistrictManager, study_with_sets: FileStudy
    ) -> None:
        district_creation = DistrictCreation(name="d1", output=True, comments="", areas=[])
        with pytest.raises(DistrictAlreadyExist):
            manager.create_district(study_with_sets, district_creation)

    def test_create_district__area_not_found(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        district_creation = DistrictCreation(
            name="d4",
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.create_district(study_with_sets, district_creation)

    def test_create_district__nominal(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        with patch.object(study_with_sets, "add_commands", wraps=study_with_sets.add_commands) as add_commands_mock:
            dto = DistrictCreation(
                name="D4",
                output=True,
                comments="hello",
                areas=["n1", "n2", "n2"],  # areas can have duplicates
            )
            actual = manager.create_district(study_with_sets, dto)
            expected = DistrictDTO(
                id="d4",
                name="D4",
                areas=["n1", "n2"],
                output=True,
                comments="hello",
            )
            actual.areas.sort()
            assert actual == expected
            _check_add_commands(add_commands_mock, CreateDistrict)

    def test_update_district__district_not_found(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        dto = DistrictUpdate(output=True, comments="", areas=[])
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.update_district(study_with_sets, "MISSING", dto)

    def test_update_district__area_not_found(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        dto = DistrictUpdate(
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.update_district(study_with_sets, "d1", dto)

    def test_update_district__nominal(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        with patch.object(study_with_sets, "add_commands", wraps=study_with_sets.add_commands) as add_commands_mock:
            dto = DistrictUpdate(
                output=True,
                comments="",
                areas=["n2", "n3"],
            )
            manager.update_district(study_with_sets, "d1", dto)
            _check_add_commands(add_commands_mock, UpdateDistrict)

    def test_remove_district__district_not_found(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.remove_district(study_with_sets, district_id="MISSING")

    def test_remove_district__nominal(self, manager: DistrictManager, study_with_sets: FileStudy) -> None:
        with patch.object(study_with_sets, "add_commands", wraps=study_with_sets.add_commands) as add_commands_mock:
            manager.remove_district(study_with_sets, district_id="d1")
            _check_add_commands(add_commands_mock, RemoveDistrict)
