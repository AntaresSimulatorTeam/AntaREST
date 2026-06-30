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
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_9_3, STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_symmetries import (
    ReplaceThermalReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create 2 areas
    cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    cmd2 = CreateArea(area_name="de", command_context=command_context, study_version=version)
    output = cmd1.apply(dao)
    assert output.status
    output = cmd2.apply(dao)
    assert output.status
    # Create 2 thermals inside area `fr` and 1 inside area `de`
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="th1"),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="th2"),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status
    cmd = CreateCluster(
        area_id="de",
        parameters=ThermalClusterCreation(name="th_de"),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status
    # Create 2 reserves inside area `fr` and 1 inside area `de`
    cmd = CreateReserveDefinition(
        area_id="fr",
        parameters=ReserveDefinitionCreation(name="r1", type=ReserveType.UP),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status
    cmd = CreateReserveDefinition(
        area_id="fr",
        parameters=ReserveDefinitionCreation(name="r2", type=ReserveType.DOWN),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status
    cmd = CreateReserveDefinition(
        area_id="de",
        parameters=ReserveDefinitionCreation(name="reserve_DE", type=ReserveType.UP),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status


def test_nominal_case(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_0, command_context)


def test_error_cases(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_0, command_context)

    # Wrong version
    with pytest.raises(ValueError, match="study version before 10.0"):
        ReplaceThermalReserveSymmetries(
            area_id="fr",
            symmetries={"th1": [["r1", "r2"]]},
            command_context=command_context,
            study_version=STUDY_VERSION_9_3,
        )

    # Wrong area
    cmd = ReplaceThermalReserveSymmetries(
        area_id="fake_area",
        symmetries={"th1": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message

    # Wrong reserve
    cmd = ReplaceThermalReserveSymmetries(
        area_id="fr",
        symmetries={"th1": [["fake_reserve", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    assert "Reserve definition 'fake_reserve' not found in area 'fr'" in output.message

    # Wrong cluster
    cmd = ReplaceThermalReserveSymmetries(
        area_id="fr",
        symmetries={"fake_thermal": [["r1", "r2"]]},
        command_context=command_context,
        study_version=STUDY_VERSION_10_0,
    )
    output = cmd.apply(dao_10_0)
    assert not output.status
    assert "Thermal cluster 'fake_thermal' not found in area 'fr'" in output.message
