# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from pydantic import ValidationError

from antarest.study.dao.memory.in_memory_study_dao import InMemoryStudyDao
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import (
    transform_name_to_id,
)
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateLink:
    def test_validation(self, command_context: CommandContext):
        area1 = "Area1"

        with pytest.raises(ValidationError):
            CreateLink(
                area1=area1,
                area2=area1,
                parameters={},
                command_context=command_context,
                series=[[0]],
                study_version=STUDY_VERSION_8_8,
            )

    def test_apply(self, command_context: CommandContext):
        study_dao = InMemoryStudyDao(STUDY_VERSION_8_8)
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        create_link_command: ICommand = CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
            study_version=study_dao.get_version(),
        )
        output = create_link_command.apply(
            study_data=study_dao,
        )

        assert output.status

        link_data = study_dao.get_link(area1_id, area2_id)
        assert link_data.hurdles_cost is False
        assert link_data.loop_flow is False
        assert link_data.use_phase_shifter is False
        assert link_data.transmission_capacities == "enabled"
        assert link_data.asset_type == "ac"
        assert link_data.link_style == "plain"
        assert link_data.link_width == 1
        assert link_data.colorr == 112
        assert link_data.colorg == 112
        assert link_data.colorb == 112
        assert link_data.display_comments is True
