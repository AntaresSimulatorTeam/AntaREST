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

import typing as t

from typing_extensions import override

from antarest.study.business.model.area_model import UpdateAreaUi
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateAreaUI(ICommand):
    """
    Command used to move an area inside the map and to update its UI.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_AREA_UI

    # Command parameters
    # ==================

    area_id: str
    area_ui: UpdateAreaUi
    layer: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:  # type: ignore
        pass

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        current_area = study_data.tree.get(["input", "areas", self.area_id, "ui"])

        if self.layer == "0":
            ui = current_area["ui"]
            ui["x"] = self.area_ui.x
            ui["y"] = self.area_ui.y
            ui["color_r"], ui["color_g"], ui["color_b"] = self.area_ui.color_rgb
        current_area["layerX"][self.layer] = self.area_ui.x
        current_area["layerY"][self.layer] = self.area_ui.y
        current_area["layerColor"][self.layer] = ",".join(map(str, self.area_ui.color_rgb))

        study_data.tree.save(current_area, ["input", "areas", self.area_id, "ui"])

        return CommandOutput(status=True, message=f"area '{self.area_id}' UI updated")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREA_UI.value,
            args={"area_id": self.area_id, "area_ui": self.area_ui, "layer": self.layer},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
