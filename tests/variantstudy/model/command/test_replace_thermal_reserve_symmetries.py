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

from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(dao: StudyDao, command_context: CommandContext) -> None:
    version = dao.get_version()
    # Create 2 areas
    cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=version)
    cmd2 = CreateArea(area_name="de", command_context=command_context, study_version=version)
    cmd1.apply(dao)
    cmd2.apply(dao)
    # Create 2 thermals inside area `fr` and 1 inside area `de`
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="th1"),
        command_context=command_context,
        study_version=version,
    )
    cmd.apply(dao)
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="th2"),
        command_context=command_context,
        study_version=version,
    )
    cmd.apply(dao)
    cmd = CreateCluster(
        area_id="de",
        parameters=ThermalClusterCreation(name="th_de"),
        command_context=command_context,
        study_version=version,
    )
    cmd.apply(dao)


def test_nominal_case(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    _set_up(dao_10_0, command_context)


def test_error_cases(dao_10_0: StudyDao, command_context: CommandContext) -> None:
    pass
