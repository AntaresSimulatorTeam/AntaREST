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
from unittest.mock import Mock

import pytest
from antares.study.version import StudyVersion
from pydantic import ValidationError

from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionCreation,
    ReserveDefinitionUpdate,
    ReserveType,
)
from antarest.study.dao.memory.in_memory_study_dao import InMemoryStudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.remove_reserve_definitions import RemoveReserveDefinitions
from antarest.study.storage.variantstudy.model.command.update_reserve_definitions import UpdateReserveDefinitions
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.utils import save_area


def _make_dao(version: StudyVersion = STUDY_VERSION_10_0) -> InMemoryStudyDao:
    return InMemoryStudyDao(version=version, matrix_service=Mock())


class TestCreateReserveDefinition:
    def test_apply(self, command_context: CommandContext) -> None:
        dao = _make_dao()
        save_area(dao, "paris")

        command = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="Reserve 1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao)
        assert output.status
        assert isinstance(output.result, ReserveDefinition)
        assert output.result.id == "reserve 1"
        assert output.result.type == ReserveType.UP

        assert dao.reserve_definition_exists("paris", "reserve 1")

    def test_apply_duplicate_fails(self, command_context: CommandContext) -> None:
        dao = _make_dao()
        save_area(dao, "paris")

        first = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="Reserve 1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        first.apply(dao)

        second = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="Reserve 1", type=ReserveType.DOWN),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = second.apply(dao)
        assert not output.status
        assert "already exists" in output.message

    def test_version_check(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="study version before 10.0"):
            CreateReserveDefinition(
                area_id="paris",
                parameters=ReserveDefinitionCreation(name="Reserve 1", type=ReserveType.UP),
                command_context=command_context,
                study_version=StudyVersion.parse("9.2"),
            )

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="Reserve 1", type=ReserveType.UP, failure_cost=500.0),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "create_reserve_definition"
        assert dto.args["area_id"] == "paris"
        assert dto.args["parameters"]["name"] == "Reserve 1"
        assert dto.args["parameters"]["type"] == "up"
        assert dto.args["parameters"]["failureCost"] == 500.0


class TestUpdateReserveDefinitions:
    def _seed(self, command_context: CommandContext) -> InMemoryStudyDao:
        dao = _make_dao()
        save_area(dao, "paris")
        CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="R1", type=ReserveType.UP, failure_cost=10.0),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        ).apply(dao)
        CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="R2", type=ReserveType.DOWN),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        ).apply(dao)
        return dao

    def test_apply(self, command_context: CommandContext) -> None:
        dao = self._seed(command_context)

        command = UpdateReserveDefinitions(
            reserve_properties={
                "paris": {
                    "r1": ReserveDefinitionUpdate(failure_cost=999.0),
                    "r2": ReserveDefinitionUpdate(spillage_cost=5.0),
                }
            },
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao)
        assert output.status

        assert dao.get_reserve_definition("paris", "r1").failure_cost == 999.0
        assert dao.get_reserve_definition("paris", "r2").spillage_cost == 5.0

    def test_apply_not_found(self, command_context: CommandContext) -> None:
        dao = self._seed(command_context)

        command = UpdateReserveDefinitions(
            reserve_properties={"paris": {"unknown": ReserveDefinitionUpdate(failure_cost=1.0)}},
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao)
        assert not output.status
        assert "'unknown'" in output.message

    def test_version_check(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="study version before 10.0"):
            UpdateReserveDefinitions(
                reserve_properties={"paris": {"R1": ReserveDefinitionUpdate(failure_cost=1.0)}},
                command_context=command_context,
                study_version=StudyVersion.parse("9.2"),
            )

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = UpdateReserveDefinitions(
            reserve_properties={"paris": {"R1": ReserveDefinitionUpdate(failure_cost=999.0)}},
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "update_reserve_definitions"
        assert dto.args["reserve_properties"]["paris"]["R1"]["failureCost"] == 999.0


class TestRemoveReserveDefinitions:
    def test_apply(self, command_context: CommandContext) -> None:
        dao = _make_dao()
        save_area(dao, "paris")
        CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(name="R1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        ).apply(dao)

        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=["r1"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao)
        assert output.status
        assert not dao.reserve_definition_exists("paris", "r1")

    def test_not_found(self, command_context: CommandContext) -> None:
        dao = _make_dao()
        save_area(dao, "paris")

        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=["unknown"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao)
        assert not output.status
        assert "do not exist" in output.message

    def test_version_check(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="study version before 10.0"):
            RemoveReserveDefinitions(
                area_id="paris",
                reserve_ids=["r1"],
                command_context=command_context,
                study_version=StudyVersion.parse("9.2"),
            )

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=["r1", "r2"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "remove_reserve_definitions"
        assert dto.args["area_id"] == "paris"
        assert dto.args["reserve_ids"] == ["r1", "r2"]
