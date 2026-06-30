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

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionCreation, ReserveType
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_3, STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_certifications import (
    ReplaceThermalReserveCertifications,
)
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_symmetries import (
    ReplaceThermalReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create area `fr`
    cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    output = cmd1.apply(dao)
    assert output.status
    # Create 2 thermals inside area `fr`
    for thermal_name in ["th1", "th2"]:
        cmd = CreateCluster(
            area_id="fr",
            parameters=ThermalClusterCreation(name=thermal_name),
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


def test_nominal_case(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_0, command_context)

    # Get reserves at first to check the current state
    result = dao_10_0.get_all_thermal_reserve_certifications()
    assert result == {}

    cmd = ReplaceThermalReserveCertifications(
        area_id="fr",
        certifications={"r1": {"th1": ThermalReserveCertification()}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert output.status

    # Check the certifications
    result = dao_10_0.get_all_thermal_reserve_certifications()
    assert result == {"fr": {"r1": {"th1": ThermalReserveCertification()}}}

    cmd = ReplaceThermalReserveSymmetries(
        area_id="fr",
        symmetries={"th1": [["r2", "r3"], ["r4", "r1"]], "th2": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert output.status

    # Check the symmetries
    result = dao_10_0.get_all_thermal_reserve_symmetries()
    assert result == {"fr": {"th1": [["r2", "r3"], ["r1", "r4"]], "th2": [["r1", "r2"]]}}


def test_error_cases(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_0, command_context)

    # Wrong version
    with pytest.raises(ValueError, match="study version before 10.0"):
        ReplaceThermalReserveCertifications(
            area_id="fr",
            certifications={"r1": {"th1": ThermalReserveCertification()}},
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )

    # Wrong area
    cmd = ReplaceThermalReserveCertifications(
        area_id="fake_area",
        certifications={"r1": {"th1": ThermalReserveCertification()}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message

    # Wrong reserve
    cmd = ReplaceThermalReserveCertifications(
        area_id="fr",
        certifications={"fake_reserve": {"th1": ThermalReserveCertification()}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    assert "Reserve definitions not found: {'fr': {'fake_reserve'}}" in output.message

    # Wrong cluster
    cmd = ReplaceThermalReserveCertifications(
        area_id="fr",
        certifications={"r1": {"fake_thermal": ThermalReserveCertification()}},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    expected_msg_db = "Thermal clusters not found: {'fr': {'fake_thermal'}}"
    expected_msg_fs = "Thermal cluster 'fake_thermal' not found in area 'fr'"
    assert expected_msg_db in output.message or expected_msg_fs in output.message
