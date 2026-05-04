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
import pytest
from antares.study.version import StudyVersion
from pydantic import ValidationError

from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionCreation,
    ReserveDefinitionId,
    ReserveDefinitionUpdate,
    ReserveType,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.remove_reserve_definitions import RemoveReserveDefinitions
from antarest.study.storage.variantstudy.model.command.update_reserve_definitions import UpdateReserveDefinitions
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.utils import save_area


class TestCreateReserveDefinition:
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")

        command = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="Reserve 1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status
        assert isinstance(output.result, ReserveDefinition)
        assert output.result.id == "Reserve 1"
        assert output.result.type == ReserveType.UP

        assert dao_10_0.reserve_definition_exists("paris", "Reserve 1")

    def test_apply_duplicate_fails(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")

        first = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="Reserve 1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        first.apply(dao_10_0)

        second = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="Reserve 1", type=ReserveType.DOWN),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = second.apply(dao_10_0)
        assert not output.status
        assert "already exists" in output.message

    def test_version_check(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="study version before 10.0"):
            CreateReserveDefinition(
                area_id="paris",
                parameters=ReserveDefinitionCreation(id="Reserve 1", type=ReserveType.UP),
                command_context=command_context,
                study_version=StudyVersion.parse("9.2"),
            )

    def test_to_dto(self, command_context: CommandContext) -> None:
        command = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="Reserve 1", type=ReserveType.UP, failure_cost=500.0),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "create_reserve_definition"
        assert dto.args["area_id"] == "paris"
        assert dto.args["parameters"]["id"] == "Reserve 1"
        assert dto.args["parameters"]["type"] == "up"
        assert dto.args["parameters"]["failureCost"] == 500.0

    def test_apply_creates_default_need_matrix(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")

        command = CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="R1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status

        matrix = dao_10_0.get_reserve_need("paris", "R1")
        assert matrix.shape == (8760, 1)
        assert matrix.to_numpy().sum() == 0.0


def _seed_two_reserves(dao: StudyDao, command_context: CommandContext) -> None:
    save_area(dao, "paris")
    CreateReserveDefinition(
        area_id="paris",
        parameters=ReserveDefinitionCreation(id="R1", type=ReserveType.UP, failure_cost=10.0),
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    ).apply(dao)
    CreateReserveDefinition(
        area_id="paris",
        parameters=ReserveDefinitionCreation(id="R2", type=ReserveType.DOWN),
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    ).apply(dao)


class TestUpdateReserveDefinitions:
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _seed_two_reserves(dao_10_0, command_context)

        command = UpdateReserveDefinitions(
            reserve_properties={
                "paris": {
                    "R1": ReserveDefinitionUpdate(failure_cost=999.0),
                    "R2": ReserveDefinitionUpdate(spillage_cost=5.0),
                }
            },
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status

        assert dao_10_0.get_reserve_definition("paris", "R1").failure_cost == 999.0
        assert dao_10_0.get_reserve_definition("paris", "R2").spillage_cost == 5.0

    def test_apply_not_found(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        _seed_two_reserves(dao_10_0, command_context)

        command = UpdateReserveDefinitions(
            reserve_properties={"paris": {"unknown": ReserveDefinitionUpdate(failure_cost=1.0)}},
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
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
    def test_apply(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")
        CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="R1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        ).apply(dao_10_0)

        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=["R1"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status
        assert not dao_10_0.reserve_definition_exists("paris", "R1")

    def test_not_found(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")

        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=["unknown"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert not output.status
        assert "not found" in output.message

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
            reserve_ids=["R1", "R2"],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        dto = command.to_dto()
        assert dto.action == "remove_reserve_definitions"
        assert dto.args["area_id"] == "paris"
        assert dto.args["reserve_ids"] == ["R1", "R2"]

    def test_apply_removes_need_matrix(self, dao_10_0: StudyDao, command_context: CommandContext) -> None:
        save_area(dao_10_0, "paris")
        CreateReserveDefinition(
            area_id="paris",
            parameters=ReserveDefinitionCreation(id="R1", type=ReserveType.UP),
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        ).apply(dao_10_0)

        reserve_id = ReserveDefinitionId("R1")
        assert dao_10_0.get_all_reserve_needs().get("paris", {}).get(reserve_id) is not None

        command = RemoveReserveDefinitions(
            area_id="paris",
            reserve_ids=[reserve_id],
            command_context=command_context,
            study_version=STUDY_VERSION_10_0,
        )
        output = command.apply(dao_10_0)
        assert output.status

        assert reserve_id not in dao_10_0.get_all_reserve_needs().get("paris", {})
