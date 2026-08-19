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
from antarest.study.storage.variantstudy.model.command.replace_st_storage_reserve_symmetries import (
    ReplaceStStorageReserveSymmetries,
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
    # A storage can only be symmetric on reserves it is certified for, so certify every pair.
    cmd = ReplaceStStorageReserveCertifications(
        area_id="fr",
        certifications={
            reserve_name: {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()}
            for reserve_name in ["r1", "r2", "r3", "r4"]
        },
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status


def test_nominal_case(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    # Get reserves at first to check the current state
    result = dao_10_2.get_all_st_storage_reserve_symmetries()
    assert result == {}

    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries={"sts1": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    # Check the symmetries
    result = dao_10_2.get_all_st_storage_reserve_symmetries()
    assert result == {"fr": {"sts1": [["r1", "r2"]]}}

    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries={"sts1": [["r2", "r3"], ["r4", "r1"]], "sts2": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    # Check the symmetries
    result = dao_10_2.get_all_st_storage_reserve_symmetries()
    assert result == {"fr": {"sts1": [["r2", "r3"], ["r1", "r4"]], "sts2": [["r1", "r2"]]}}

    # Ensures replacing existing data with new one erases the old values
    new_symmetries = {"sts2": [["r1", "r3", "r4"]]}

    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries=new_symmetries,
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    result = dao_10_2.get_st_storage_reserve_symmetries("fr")
    assert result == new_symmetries

    # Ensures we're able to remove all symmetries
    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries={},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert output.status

    result = dao_10_2.get_st_storage_reserve_symmetries("fr")
    assert result == {}


def test_study_version_sould_be_at_least_10_2_for_reserves(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    with pytest.raises(ValueError, match="study version before 10.2"):
        ReplaceStStorageReserveSymmetries(
            area_id="fr",
            symmetries={"sts1": [["r1", "r2"]]},
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )


def test_area_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fake_area",
        symmetries={"sts1": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message


def test_reserve_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries={"sts1": [["fake_reserve", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Reserve definition 'fake_reserve' not found in area 'fr'" in output.message


def test_short_term_storage_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    # Wrong short-term storage
    cmd = ReplaceStStorageReserveSymmetries(
        area_id="fr",
        symmetries={"fake_storage": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Short-term storage 'fake_storage' not found in area 'fr'" in output.message
