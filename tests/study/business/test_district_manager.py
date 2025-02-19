# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from unittest.mock import Mock

import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import AreaNotFound, DistrictAlreadyExist, DistrictNotFound
from antarest.study.business.district_manager import (
    DistrictCreationDTO,
    DistrictInfoDTO,
    DistrictManager,
    DistrictUpdateDTO,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import DistrictSet
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# noinspection SpellCheckingInspection
EXECUTE_OR_ADD_COMMANDS = "antarest.study.business.district_manager.execute_or_add_commands"


def _check_add_commands(patched_func, expected_cls):
    assert patched_func.call_count == 1
    commands = patched_func.mock_calls[0].args[0]
    command = commands[0]
    assert isinstance(command, expected_cls)


@pytest.fixture
def manager(command_context: CommandContext) -> DistrictManager:
    return DistrictManager(command_context)


def create_study_interface(file_study: FileStudy, version: StudyVersion = STUDY_VERSION_8_6) -> StudyInterface:
    """
    Creates a mock study interface which returns the provided study tree.
    """
    study = Mock(StudyInterface)
    study.get_files.return_value = file_study
    study.version = version
    file_study.config.version = version
    return study


class TestDistrictManager:
    def test_get_districts(self, manager: DistrictManager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=[], output=True),
            "d2": DistrictSet(name="D2", areas=["n1", "n2"], output=True),
            "d3": DistrictSet(name="D2", areas=["n1", "n2", "n3"], output=False),
        }

        # mocks
        file_study_tree = Mock(spec=FileStudyTree)
        file_study_tree.get.return_value = {"comments": "dummy"}  # same comment for all nodes
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=file_study_tree,
        )
        study = create_study_interface(file_study)

        # run
        actual = manager.get_districts(study)
        expected = [
            DistrictInfoDTO(
                id="d1",
                name="D1",
                areas=[],
                output=True,
                comments="dummy",
            ),
            DistrictInfoDTO(
                id="d2",
                name="D2",
                areas=["n1", "n2"],
                output=True,
                comments="dummy",
            ),
            DistrictInfoDTO(
                id="d3",
                name="D2",
                areas=["n1", "n2", "n3"],
                output=False,
                comments="dummy",
            ),
        ]
        assert actual == expected

    def test_create_district__district_already_exist(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=[], output=True),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study)

        # run
        dto = DistrictCreationDTO(name="d1", output=True, comments="", areas=[])
        with pytest.raises(DistrictAlreadyExist):
            manager.create_district(study, dto)

    def test_create_district__area_not_found(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study)

        # run
        dto = DistrictCreationDTO(
            name="d1",
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.create_district(study, dto)

    def test_create_district__nominal(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "all areas": DistrictSet(name="All areas", areas=["n1", "n2", "n3"], output=False),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        file_study.config.version = STUDY_VERSION_8_8
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        dto = DistrictCreationDTO(
            name="D1",
            output=True,
            comments="hello",
            areas=["n1", "n2", "n2"],  # areas can have duplicates
        )
        actual = manager.create_district(study, dto)
        expected = DistrictInfoDTO(
            id="d1",
            name="D1",
            areas=["n1", "n2"],
            output=True,
            comments="hello",
        )
        actual.areas.sort()
        assert actual == expected
        _check_add_commands(study.add_commands, CreateDistrict)

    def test_update_district__district_not_found(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        dto = DistrictUpdateDTO(output=True, comments="", areas=[])
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.update_district(study, "MISSING", dto)

    def test_update_district__area_not_found(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=["n1", "n2", "n3"], output=False),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        dto = DistrictUpdateDTO(
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.update_district(study, "d1", dto)

    def test_update_district__nominal(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=["n1", "n2", "n3"], output=False),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        dto = DistrictUpdateDTO(
            output=True,
            comments="",
            areas=["n2", "n3"],
        )
        manager.update_district(study, "d1", dto)
        _check_add_commands(study.add_commands, UpdateDistrict)

    def test_remove_district__district_not_found(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.remove_district(study, district_id="MISSING")

    def test_remove_district__nominal(self, manager):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=["n1", "n2", "n3"], output=False),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        study = create_study_interface(file_study, version=STUDY_VERSION_8_8)

        # run
        manager.remove_district(study, district_id="d1")
        _check_add_commands(study.add_commands, RemoveDistrict)
