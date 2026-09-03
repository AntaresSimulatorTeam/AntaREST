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
from antarest.study.storage.variantstudy.model.command.replace_hydro_reserve_certifications import (
    ReplaceHydroReserveCertifications,
)
from antarest.study.storage.variantstudy.model.command.replace_hydro_reserve_symmetries import (
    ReplaceHydroReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create area `fr`. It owns its long-term storage, so there is no asset to create.
    cmd = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    assert cmd.apply(dao).status
    # Create 3 reserves inside area `fr`
    for reserve_name in ["r1", "r2", "r3"]:
        cmd = CreateReserveDefinition(
            area_id="fr",
            parameters=ReserveDefinitionCreation(name=reserve_name, type=ReserveType.UP),
            command_context=command_context,
            study_version=version,
        )
        assert cmd.apply(dao).status
    # Symmetries are only valid on certified reserves
    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={r: StorageReserveCertification() for r in ["r1", "r2", "r3"]},
        command_context=command_context,
        study_version=version,
    )
    assert cmd.apply(dao).status


def test_nominal_case(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    assert dao_10_2.get_all_hydro_reserve_symmetries() == {}

    cmd = ReplaceHydroReserveSymmetries(
        area_id="fr",
        symmetries=[["r1", "r2"]],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    assert cmd.apply(dao_10_2).status
    assert dao_10_2.get_all_hydro_reserve_symmetries() == {"fr": [["r1", "r2"]]}

    # Replacing existing data with new one erases the old values
    cmd = ReplaceHydroReserveSymmetries(
        area_id="fr",
        symmetries=[["r2", "r3"]],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    assert cmd.apply(dao_10_2).status
    assert dao_10_2.get_hydro_reserve_symmetries("fr") == [["r2", "r3"]]

    # We're able to remove all symmetries
    cmd = ReplaceHydroReserveSymmetries(
        area_id="fr",
        symmetries=[],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    assert cmd.apply(dao_10_2).status
    assert dao_10_2.get_hydro_reserve_symmetries("fr") == []


def test_symmetries_are_sorted_and_reject_duplicates(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceHydroReserveSymmetries(
        area_id="fr",
        symmetries=[["r2", "r1"]],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    assert cmd.apply(dao_10_2).status
    assert dao_10_2.get_hydro_reserve_symmetries("fr") == [["r1", "r2"]]

    with pytest.raises(ValueError, match="should not contain duplicates"):
        ReplaceHydroReserveSymmetries(
            area_id="fr",
            symmetries=[["r1", "r1"]],
            command_context=command_context,
            study_version=STUDY_VERSION_10_2,
        )

    with pytest.raises(ValueError, match="at least 2 elements"):
        ReplaceHydroReserveSymmetries(
            area_id="fr",
            symmetries=[["r1"]],
            command_context=command_context,
            study_version=STUDY_VERSION_10_2,
        )


def test_study_version_should_be_at_least_10_2_for_reserves(
    dao_10_2: StudyDao, command_context: CommandContext
) -> None:
    _set_up(dao_10_2, command_context)

    with pytest.raises(ValueError, match="study version before 10.2"):
        ReplaceHydroReserveSymmetries(
            area_id="fr",
            symmetries=[["r1", "r2"]],
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )


def test_area_should_be_valid(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    cmd = ReplaceHydroReserveSymmetries(
        area_id="fake_area",
        symmetries=[["r1", "r2"]],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message


def test_reserve_should_be_certified(dao_10_2: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_2, command_context)

    # Drop `r3`'s certification, then try to build a symmetry on it
    cmd = ReplaceHydroReserveCertifications(
        area_id="fr",
        certifications={r: StorageReserveCertification() for r in ["r1", "r2"]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    assert cmd.apply(dao_10_2).status

    cmd = ReplaceHydroReserveSymmetries(
        area_id="fr",
        symmetries=[["r1", "r3"]],
        command_context=command_context,
        study_version=STUDY_VERSION_10_2,
    )
    output = cmd.apply(dao_10_2)
    assert not output.status
    assert "r3" in output.message
