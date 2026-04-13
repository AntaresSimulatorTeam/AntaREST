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

from antarest.study.business.model.reserves_global_parameters_model import (
    ReservesGlobalParametersUpdate,
)
from antarest.study.dao.memory.in_memory_study_dao import InMemoryStudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.update_reserves_global_parameters import (
    UpdateReservesGlobalParameters,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _make_dao(version: StudyVersion = STUDY_VERSION_10_0) -> InMemoryStudyDao:
    return InMemoryStudyDao(version=version, matrix_service=Mock())


def test_apply_command(command_context: CommandContext) -> None:
    dao = _make_dao()
    area_id = "paris"
    dao.save_area(area_id)

    update = ReservesGlobalParametersUpdate(
        reference_activation_duration_up=5,
        energy_activation_ratio_up=0.5,
    )
    command = UpdateReservesGlobalParameters(
        properties={area_id: update},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = command.apply(dao)
    assert output.status

    result = dao.get_reserves_global_parameters(area_id)
    assert result.reference_activation_duration_up == 5
    assert result.energy_activation_ratio_up == 0.5
    assert result.reference_activation_duration_down == 1
    assert result.energy_activation_ratio_down == 1.0


def test_apply_multiple_areas(command_context: CommandContext) -> None:
    dao = _make_dao()
    dao.save_area("paris")
    dao.save_area("lyon")

    command = UpdateReservesGlobalParameters(
        properties={
            "paris": ReservesGlobalParametersUpdate(reference_activation_duration_up=5),
            "lyon": ReservesGlobalParametersUpdate(energy_activation_ratio_down=0.3),
        },
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = command.apply(dao)
    assert output.status

    paris = dao.get_reserves_global_parameters("paris")
    assert paris.reference_activation_duration_up == 5
    assert paris.energy_activation_ratio_up == 1.0

    lyon = dao.get_reserves_global_parameters("lyon")
    assert lyon.energy_activation_ratio_down == 0.3
    assert lyon.reference_activation_duration_down == 1


def test_area_not_found(command_context: CommandContext) -> None:
    dao = _make_dao()

    command = UpdateReservesGlobalParameters(
        properties={"nonexistent": ReservesGlobalParametersUpdate(reference_activation_duration_up=5)},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = command.apply(dao)
    assert not output.status


def test_version_check(command_context: CommandContext) -> None:
    with pytest.raises(ValidationError, match="study version before 10.0"):
        UpdateReservesGlobalParameters(
            properties={"paris": ReservesGlobalParametersUpdate(reference_activation_duration_up=5)},
            command_context=command_context,
            study_version=StudyVersion.parse("9.2"),
        )


def test_to_dto(command_context: CommandContext) -> None:
    update = ReservesGlobalParametersUpdate(
        reference_activation_duration_up=5,
        energy_activation_ratio_up=0.5,
    )
    command = UpdateReservesGlobalParameters(
        properties={"paris": update},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    dto = command.to_dto()
    assert dto.action == "update_reserves_global_parameters"
    assert dto.args["properties"]["paris"]["reference_activation_duration_up"] == 5
    assert dto.args["properties"]["paris"]["energy_activation_ratio_up"] == 0.5
