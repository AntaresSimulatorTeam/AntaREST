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
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.area_model import AreaUIUpdate
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

    @field_validator("layer")
    @classmethod
    def _validate_layer(cls, v: str) -> str:
        """Validate that layer is a valid integer string."""
        try:
            int(v)
            return v
        except ValueError:
            raise ValueError(f"Layer must be a valid integer string, got: {v}")

    @model_validator(mode="before")
    @classmethod
    def _validate_parameters(cls, values: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        # Handle version 1 format: {"area_id": "x", "area_ui": {...}, "layer": "0"}
        if "area_ui" in values:
            area_ui = values.pop("area_ui")
            # Extract only x, y, color_rgb from old UpdateAreaUi (ignore layer_x, layer_y, layer_color)
            if isinstance(area_ui, dict):
                color_value = area_ui.get("color_rgb") or area_ui.get("colorRgb")
                # Convert list to tuple if necessary
                if color_value is not None and isinstance(color_value, list):
                    color_value = tuple(color_value)

                parameters = {
                    "x": area_ui.get("x"),
                    "y": area_ui.get("y"),
                    "color_rgb": color_value,
                }
                # Remove None values
                parameters = {k: v for k, v in parameters.items() if v is not None}
                values["parameters"] = parameters
            else:
                # If it's already a pydantic model
                values["parameters"] = {
                    "x": area_ui.x if hasattr(area_ui, "x") else None,
                    "y": area_ui.y if hasattr(area_ui, "y") else None,
                    "color_rgb": area_ui.color_rgb if hasattr(area_ui, "color_rgb") else None,
                }
                values["parameters"] = {k: v for k, v in values["parameters"].items() if v is not None}

        # Ensure parameters exists
        if "parameters" not in values:
            values["parameters"] = AreaUIUpdate()

        return values

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        current_area = study_data.tree.get(["input", "areas", self.area_id, "ui"])
        layer_int = int(self.layer)

        # Apply updates if provided
        if self.parameters.x is not None:
            current_area["layerX"][self.layer] = self.parameters.x
            if layer_int == 0:
                current_area["ui"]["x"] = self.parameters.x

        if self.parameters.y is not None:
            current_area["layerY"][self.layer] = self.parameters.y
            if layer_int == 0:
                current_area["ui"]["y"] = self.parameters.y

        if self.parameters.color_rgb is not None:
            r, g, b = self.parameters.color_rgb
            current_area["layerColor"][self.layer] = f"{r}, {g}, {b}"
            if layer_int == 0:
                current_area["ui"]["color_r"] = r
                current_area["ui"]["color_g"] = g
                current_area["ui"]["color_b"] = b

        study_data.tree.save(current_area, ["input", "areas", self.area_id, "ui"])

        return command_succeeded(message=f"area '{self.area_id}' UI updated")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREA_UI.value,
            args={
                "area_id": self.area_id,
                "layer": self.layer,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
            version=2,
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
