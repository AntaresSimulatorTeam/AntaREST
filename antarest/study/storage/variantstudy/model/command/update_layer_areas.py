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

import re
from typing import Any, Dict, List, Optional

from typing_extensions import override

from antarest.core.exceptions import LayerNotFound
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


def _get_area_layers(area_uis: Dict[str, Any], area: str) -> List[str]:
    """Extract the list of layers from an area's UI configuration."""
    if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
        return re.split(r"\s+", (str(area_uis[area]["ui"]["layers"]) or ""))
    return []


class UpdateLayerAreas(ICommand):
    """
    Command used to update the areas associated with a specific layer.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LAYER_AREAS

    # Command parameters
    # ==================

    layer_id: str
    area_ids: List[str]

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Verify that the layer exists
        layers = study_data.tree.get(["layers", "layers", "layers"])
        if self.layer_id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound

        # Get all areas UI configuration
        areas_ui = study_data.tree.get(["input", "areas", ",".join(study_data.config.areas), "ui"])

        # Standardize 'areas_ui' to a dictionary format even if only one area exists
        cfg_areas = list(study_data.config.areas)
        if len(cfg_areas) == 1:
            areas_ui = {cfg_areas[0]: areas_ui}

        # Determine which areas currently have this layer
        existing_areas = [
            area for area in areas_ui if "ui" in areas_ui[area] and self.layer_id in _get_area_layers(areas_ui, area)
        ]

        # Calculate areas to add and remove
        to_remove_areas = [area for area in existing_areas if area not in self.area_ids]
        to_add_areas = [area for area in self.area_ids if area not in existing_areas]

        # Remove layer from areas
        for area in to_remove_areas:
            area_layers = _get_area_layers(areas_ui, area)
            if self.layer_id in areas_ui[area]["layerX"]:
                del areas_ui[area]["layerX"][self.layer_id]
            if self.layer_id in areas_ui[area]["layerY"]:
                del areas_ui[area]["layerY"][self.layer_id]
            if self.layer_id in area_layers:
                areas_ui[area]["ui"]["layers"] = " ".join(
                    [layer for layer in area_layers if layer != self.layer_id]
                )

        # Add layer to areas
        for area in to_add_areas:
            area_layers = _get_area_layers(areas_ui, area)
            if self.layer_id not in areas_ui[area]["layerX"]:
                areas_ui[area]["layerX"][self.layer_id] = areas_ui[area]["ui"]["x"]
            if self.layer_id not in areas_ui[area]["layerY"]:
                areas_ui[area]["layerY"][self.layer_id] = areas_ui[area]["ui"]["y"]
            if self.layer_id not in area_layers:
                areas_ui[area]["ui"]["layers"] = " ".join(area_layers + [self.layer_id])

        # Save all modified areas
        for area in to_remove_areas + to_add_areas:
            study_data.tree.save(areas_ui[area], ["input", "areas", area, "ui"])

        return command_succeeded(message=f"Layer '{self.layer_id}' areas updated")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_LAYER_AREAS.value,
            args={
                "layer_id": self.layer_id,
                "area_ids": self.area_ids,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
