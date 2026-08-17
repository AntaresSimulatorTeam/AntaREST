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
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.replace_st_storage_reserve_certifications import (
    ReplaceStStorageReserveCertifications,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create area `fr`
    cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    output = cmd1.apply(dao)
    assert output.status
    # Create 2 short-term storages inside area `fr`
    for storage_name in ["sts1", "sts2"]:
        cmd = CreateSTStorage(
            area_id="fr",
            parameters={"name": storage_name},
            command_context=command_context,
            study_version=version,
        )
        output = cmd.apply(dao)
        assert output.status
    # Create 4 reserves inside area `fr`
    for reserve_name in ["r1", "r2", "r3", "r4"]:
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

    # Get reserves at first to check the current state
    result = dao_10_2.get_all_st_storage_reserve_certifications()
    assert result == {}

    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications={"r1": {"sts1": StorageReserveCertification()}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    # Check the certifications
    result = dao_10_2.get_all_st_storage_reserve_certifications()
    assert result == {"fr": {"r1": {"sts1": StorageReserveCertification()}}}

    new_certifications = {
        "r1": {
            "sts1": StorageReserveCertification(participation_cost=10.5, max_release=6, max_store=21),
            "sts2": StorageReserveCertification(),
        },
        "r2": {"sts2": StorageReserveCertification(participation_cost=1000, max_release=1)},
    }

    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications=new_certifications,
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    # Check the certifications
    result = dao_10_2.get_st_storage_reserve_certifications("fr")
    assert result == new_certifications

    # Ensures replacing existing data with new one erases the old values
    new_certifications = {"r2": {"sts1": StorageReserveCertification(participation_cost=4, max_release=1.2)}}

    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications=new_certifications,
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    result = dao_10_2.get_st_storage_reserve_certifications("fr")
    assert result == new_certifications

    # Ensures we're able to remove all certifications
    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications={},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    result = dao_10_2.get_st_storage_reserve_certifications("fr")
    assert result == {}


def test_study_version_sould_be_at_least_10_2_for_reserves(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    certification = StorageReserveCertification()
    # Wrong version
    with pytest.raises(ValueError, match="study version before 10.2"):
        ReplaceStStorageReserveCertifications(
            area_id="fr",
            certifications={"r1": {"sts1": certification}},
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )


def test_area_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    certification = StorageReserveCertification()
    # Wrong area
    cmd = ReplaceStStorageReserveCertifications(
        area_id="fake_area",
        certifications={"r1": {"sts1": certification}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message


def test_reserve_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    certification = StorageReserveCertification()

    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications={"fake_reserve": {"sts1": certification}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Reserve definitions not found: {'fr': {'fake_reserve'}}" in output.message


def test_st_storage_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    certification = StorageReserveCertification()

    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications={"r1": {"fake_storage": certification}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    expected_msg_db = "Short term storages not found: {'fr': {'fake_storage'}}"
    expected_msg_fs = "Short-term storage 'fake_storage' not found in area 'fr'"
    assert expected_msg_db in output.message or expected_msg_fs in output.message
