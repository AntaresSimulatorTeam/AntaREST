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

from antarest.core.exceptions import LinkValidationError
from antarest.core.serde.ini_reader import IniReader
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateLink:
    def test_validation(self, empty_study: FileStudy, command_context: CommandContext):
        area1 = "Area1"
        area2 = "Area2"

        CreateArea.model_validate(
            {"area_name": area1, "command_context": command_context, "study_version": STUDY_VERSION_8_8}
        ).apply(empty_study)

        CreateArea.model_validate(
            {"area_name": area2, "command_context": command_context, "study_version": STUDY_VERSION_8_8}
        ).apply(empty_study)

        with pytest.raises(ValidationError):
            CreateLink(
                area1=area1,
                area2=area1,
                parameters={},
                command_context=command_context,
                series=[[0]],
                study_version=STUDY_VERSION_8_8,
            )

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        study_version = empty_study.config.version
        study_path = empty_study.config.study_path
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        area3 = "Area3"
        area3_id = transform_name_to_id(area3)

        CreateArea.model_validate(
            {"area_name": area1, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        CreateArea.model_validate(
            {"area_name": area2, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        CreateArea.model_validate(
            {"area_name": area3, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        create_link_command: ICommand = CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
            study_version=study_version,
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (study_path / "input" / "links" / area1_id / f"{area2_id}.txt.link").exists()

        link = IniReader()
        link_data = link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert link_data[area2_id]["hurdles-cost"] is False
        assert link_data[area2_id]["loop-flow"] is False
        assert link_data[area2_id]["use-phase-shifter"] is False
        assert link_data[area2_id]["transmission-capacities"] == "enabled"
        assert link_data[area2_id]["asset-type"] == "ac"
        assert link_data[area2_id]["link-style"] == "plain"
        assert int(link_data[area2_id]["link-width"]) == 1
        assert int(link_data[area2_id]["colorr"]) == 112
        assert int(link_data[area2_id]["colorg"]) == 112
        assert int(link_data[area2_id]["colorb"]) == 112
        assert link_data[area2_id]["display-comments"] is True

        empty_study.config.version = 820
        create_link_command: ICommand = CreateLink(
            area1=area2_id,
            area2=area3_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
            study_version=study_version,
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert output.status
        empty_study.config.version = 800

        assert (study_path / "input" / "links" / area2_id / f"{area3_id}_parameters.txt.link").exists()
        assert (study_path / "input" / "links" / area2_id / "capacities" / f"{area3_id}_direct.txt.link").exists()
        assert (study_path / "input" / "links" / area2_id / "capacities" / f"{area3_id}_indirect.txt.link").exists()

        # TODO:assert matrix default content : 1 column, 8760 rows, value = 1

        output = CreateLink.model_validate(
            {
                "area1": area1_id,
                "area2": area2_id,
                "parameters": {},
                "command_context": command_context,
                "series": [[0]],
                "study_version": study_version,
            }
        ).apply(study_data=empty_study)

        assert not output.status

        parameters = {
            "hurdles-cost": True,
            "loop-flow": True,
            "use-phase-shifter": True,
            "transmission-capacities": "ignore",
            "asset-type": "dc",
            "link-style": "other",
            "link-width": 12,
            "colorr": 120,
            "colorg": 120,
            "colorb": 120,
            "display-comments": True,
            "filter-synthesis": "hourly",
            "filter-year-by-year": "hourly",
        }

        create_link_command: ICommand = CreateLink.model_validate(
            {
                "area1": area3_id,
                "area2": area1_id,
                "parameters": parameters,
                "command_context": command_context,
                "series": [[0]],
                "study_version": study_version,
            }
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status
        with pytest.raises(LinkValidationError):
            CreateLink.model_validate(
                {
                    "area1": area3_id,
                    "area2": area1_id,
                    "parameters": parameters,
                    "direct": [[0]],
                    "command_context": command_context,
                    "study_version": study_version,
                }
            )

        assert (study_path / "input" / "links" / area1_id / f"{area3_id}.txt.link").exists()

        link = IniReader()
        link_data = link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert link_data[area3_id]["hurdles-cost"] == parameters["hurdles-cost"]
        assert link_data[area3_id]["loop-flow"] == parameters["loop-flow"]
        assert link_data[area3_id]["use-phase-shifter"] == parameters["use-phase-shifter"]
        assert link_data[area3_id]["transmission-capacities"] == parameters["transmission-capacities"]
        assert link_data[area3_id]["asset-type"] == parameters["asset-type"]
        assert link_data[area3_id]["link-style"] == parameters["link-style"]
        assert int(link_data[area3_id]["link-width"]) == parameters["link-width"]
        assert int(link_data[area3_id]["colorr"]) == parameters["colorr"]
        assert int(link_data[area3_id]["colorg"]) == parameters["colorg"]
        assert int(link_data[area3_id]["colorb"]) == parameters["colorb"]
        assert link_data[area3_id]["display-comments"] == parameters["display-comments"]

        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert not output.status

        output = CreateLink(
            area1="does_not_exist",
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
            study_version=study_version,
        ).apply(empty_study)
        assert not output.status
