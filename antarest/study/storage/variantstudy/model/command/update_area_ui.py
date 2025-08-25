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
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
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
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        current_area = study_data.tree.get(["input", "areas", self.area_id, "ui"])

        self._update_main_ui_if_layer_zero(current_area)
        self._update_layer_position(current_area)
        self._update_layer_color(current_area)

        study_data.tree.save(current_area, ["input", "areas", self.area_id, "ui"])

        return command_succeeded(message=f"area '{self.area_id}' UI updated")

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

    def _update_main_ui_if_layer_zero(self, current_area: dict[str, t.Any]) -> None:
        """Update the main UI properties if we're working on layer 0."""
        if self.layer != "0":
            return

        ui = current_area["ui"]
        if self.area_ui.x is not None:
            ui["x"] = self.area_ui.x
        if self.area_ui.y is not None:
            ui["y"] = self.area_ui.y
        if self.area_ui.color_rgb is not None:
            ui["color_r"], ui["color_g"], ui["color_b"] = self.area_ui.color_rgb

    def _update_layer_position(self, current_area: dict[str, t.Any]) -> None:
        """Update layer X and Y positions."""
        layer_int = int(self.layer)

        # Update X position
        if self.area_ui.layer_x is not None:
            x_value = self.area_ui.layer_x.get(layer_int, current_area["layerX"].get(self.layer))
        elif self.area_ui.x is not None:
            x_value = self.area_ui.x
        else:
            x_value = None

        if x_value is not None:
            current_area["layerX"][self.layer] = x_value

        # Update Y position
        if self.area_ui.layer_y is not None:
            y_value = self.area_ui.layer_y.get(layer_int, current_area["layerY"].get(self.layer))
        elif self.area_ui.y is not None:
            y_value = self.area_ui.y
        else:
            y_value = None

        if y_value is not None:
            current_area["layerY"][self.layer] = y_value

    def _update_layer_color(self, current_area: dict[str, t.Any]) -> None:
        """Update layer color."""
        layer_int = int(self.layer)

        if self.area_ui.layer_color is not None:
            color_value = self.area_ui.layer_color.get(layer_int, current_area["layerColor"].get(self.layer))
        elif self.area_ui.color_rgb is not None:
            color_value = ",".join(map(str, self.area_ui.color_rgb))
        else:
            color_value = None

        if color_value is not None:
            current_area["layerColor"][self.layer] = color_value
