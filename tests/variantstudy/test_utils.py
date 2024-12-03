# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO


def test_aggregate_commands(command_context: CommandContext):
    study_version = STUDY_VERSION_8_8
    command_list = [
        CreateArea(area_name="a", command_context=command_context, study_version=study_version),
        CreateArea(area_name="b", command_context=command_context, study_version=study_version),
        CreateLink(area1="a", area2="b", command_context=command_context, study_version=study_version),
        CreateArea(area_name="d", command_context=command_context, study_version=study_version),
        CreateArea(area_name="e", command_context=command_context, study_version=study_version),
    ]
    command_dto_list = transform_command_to_dto(command_list, force_aggregate=True)
    assert len(command_dto_list) == 3

    command_dto_list = transform_command_to_dto(command_list)
    assert len(command_dto_list) == 5

    command_ref_list = [
        CommandDTO(action="create_area", args=[{"area_name": "a"}, {"area_name": "b"}], study_version=study_version),
        CommandDTO(action="create_link", args={"area1": "a", "area2": "b"}, study_version=study_version),
        CommandDTO(action="create_area", args={"area_name": "d"}, study_version=study_version),
        CommandDTO(action="create_area", args={"area_name": "e"}, study_version=study_version),
    ]

    command_dto_list = transform_command_to_dto(command_list, command_ref_list)
    assert len(command_dto_list) == 4
