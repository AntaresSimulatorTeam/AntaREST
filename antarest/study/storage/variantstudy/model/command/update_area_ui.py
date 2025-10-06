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

from antarest.study.business.model.area_model import AreaUI, AreaUIUpdate, update_area_ui
from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUIFileData, AreaUIStyle
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateAreaUI(ICommand):
    """
    Command used to update an area's UI properties (position and color) for a specific layer.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_AREA_UI

    # Command parameters
    # ==================

    area_id: str
    layer: str
    parameters: AreaUIUpdate

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        # Retrieve current area UI data from file
        current_area_data = study_data.tree.get(["input", "areas", self.area_id, "ui"])
        area_ui_file_data = AreaUIFileData(**current_area_data)

        # Get current style for the specified layer
        layer_int = int(self.layer)
        current_style = area_ui_file_data.layer_styles.get(layer_int, area_ui_file_data.style)

        # Convert to business model
        current_ui = AreaUI(
            x=current_style.x,
            y=current_style.y,
            color_rgb=(current_style.color_r, current_style.color_g, current_style.color_b),
        )

        # Apply update
        updated_ui = update_area_ui(current_ui, self.parameters)

        # Convert back to file data model
        updated_style = AreaUIStyle(
            x=updated_ui.x,
            y=updated_ui.y,
            color_r=updated_ui.color_rgb[0],
            color_g=updated_ui.color_rgb[1],
            color_b=updated_ui.color_rgb[2],
        )

        # Update the appropriate style
        if layer_int == 0:
            area_ui_file_data.style = updated_style
        area_ui_file_data.layer_styles[layer_int] = updated_style

        # Save to file
        study_data.tree.save(area_ui_file_data.to_config(), ["input", "areas", self.area_id, "ui"])

        return command_succeeded(message=f"area '{self.area_id}' UI updated")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREA_UI.value,
            args={"area_id": self.area_id, "layer": self.layer, "parameters": self.parameters},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
