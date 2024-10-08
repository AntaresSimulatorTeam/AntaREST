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
import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(ICommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK
    version: int = 1

    # Command parameters
    # ==================
    area1: str
    area2: str
    parameters: t.Optional[t.Dict[str, t.Any]] = None

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        area_from, area_to = sorted([self.area1, self.area2])

        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' updated",
            ),
            {"area_from": area_from, "area_to": area_to},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        area_from, area_to = sorted([self.area1, self.area2])
        study_data.tree.save(self.parameters, ["input", "links", area_from, "properties", area_to])
        output, _ = self._apply_config(study_data.config)
        return output

    def to_dto(self) -> CommandDTO:
        args = {
            "area1": self.area1,
            "area2": self.area2,
            "parameters": self.parameters,
        }
        return CommandDTO(
            action=CommandName.UPDATE_LINK.value,
            args=args,
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.area1 + MATCH_SIGNATURE_SEPARATOR + self.area2
        )

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        pass

    def get_inner_matrices(self) -> t.List[str]:
        pass