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

from antarest.study.business.model.reserve_certification_model import StorageReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionCreation, ReserveType
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_3, STUDY_VERSION_10_2
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.replace_hydro_reserve_certifications import (
    ReplaceHydroReserveCertifications,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create area `fr`. It owns its long-term storage, so there is no asset to create.
    cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    output = cmd1.apply(dao)
    assert output.status
    # Create 3 reserves inside area `fr`
    for reserve_name in ["r1", "r2", "r3"]:
        cmd = CreateReserveDefinition(
            area_id="fr",
            parameters=ReserveDefinitionCreation(name=reserve_name, type=ReserveType.UP),
            command_context=command_context,
            study_version=version,
        )
        output = cmd.apply(dao)
        assert output.status


def test_nominal_case(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    # Get certifications at first to check the current state
    assert dao_10_2.get_all_hydro_reserve_certifications() == {}

    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={"r1": StorageReserveCertification()},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    assert dao_10_2.get_all_hydro_reserve_certifications() == {"fr": {"r1": StorageReserveCertification()}}

    new_certifications = {
        "r1": StorageReserveCertification(participation_cost=10.5, max_release=6, max_store=21),
        "r2": StorageReserveCertification(participation_cost=1000, max_release=1),
    }

    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications=new_certifications,
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    assert dao_10_2.get_hydro_reserve_certifications("fr") == new_certifications

    # Ensures replacing existing data with new one erases the old values
    new_certifications = {"r2": StorageReserveCertification(participation_cost=4, max_release=1.2)}

    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications=new_certifications,
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    assert dao_10_2.get_hydro_reserve_certifications("fr") == new_certifications

    # Ensures we're able to remove all certifications
    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    assert dao_10_2.get_hydro_reserve_certifications("fr") == {}


def test_study_version_should_be_at_least_10_2_for_reserves(
    dao_10_2: StudyDao, command_context: CommandContext
) -> None:
    _set_up(dao_10_2, command_context)

    # Wrong version
    with pytest.raises(ValueError, match="study version before 10.2"):
        ReplaceHydroReserveCertifications(
            area_id="fr",
            certifications={"r1": StorageReserveCertification()},
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )


def test_area_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceHydroReserveCertifications(
        area_id="fake_area",
        certifications={"r1": StorageReserveCertification()},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message


def test_reserve_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={"fake_reserve": StorageReserveCertification()},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Reserve definitions not found: {'fr': {'fake_reserve'}}" in output.message


def test_command_dto_round_trip(command_context: CommandContext) -> None:
    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={"r1": StorageReserveCertification(participation_cost=2.0, max_release=3.0, max_store=4.0)},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )

    dto = cmd.to_dto()
    assert dto.action == "replace_hydro_reserve_certifications"
    assert dto.args == {
        "area_id": "fr",
        "certifications": {"r1": {"participation_cost": 2.0, "max_release": 3.0, "max_store": 4.0}},
    }

    # The factory must be able to rebuild the exact same command from the DTO
    rebuilt = CommandFactory(
        generator_matrix_constants=command_context.generator_matrix_constants,
        matrix_service=command_context.matrix_service,
        blob_service=command_context.blob_service,
    ).to_command(dto)
    assert rebuilt == [cmd]
