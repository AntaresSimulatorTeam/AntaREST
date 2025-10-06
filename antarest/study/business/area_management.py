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

import logging
from typing import Any, Dict, List

from antarest.core.exceptions import DuplicateAreaName, LayerNotFound
from antarest.study.business.areas.area_utils import _get_area_layers, _get_ui_info_map
from antarest.study.business.model.area_model import (
    Area,
    AreaCreation,
    UpdateAreaUi,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class AreaManager:
    """
    Manages operations related to areas in a study, including retrieval, creation, and updates.
    """

    def __init__(
        self,
        command_context: CommandContext,
    ) -> None:
        """
        Initializes the AreaManager.
        """
        self._command_context = command_context

    def get_all_areas(self, study: StudyInterface) -> List[Area]:
        """Retrieve all physical areas of a raw study."""

        file_study = study.get_files()
        cfg_areas: Dict[str, AreaConfig] = file_study.config.areas
        return [
            Area(
                id=area_id,
                name=area.name,
                thermals=self._get_clusters(file_study, area_id),
            )
            for area_id, area in cfg_areas.items()
        ]

    def get_all_areas_ui_info(self, study: StudyInterface) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Args:
            study: The raw study object containing the study's data.

        Returns:
            A dictionary containing information about the user interface for the areas.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        file_study = study.get_files()
        area_ids = list(file_study.config.areas)
        return _get_ui_info_map(file_study, area_ids)

    def update_layer_areas(self, study: StudyInterface, layer_id: str, areas: List[str]) -> None:
        logger.info(f"Updating layer {layer_id} with areas {areas}")
        file_study = study.get_files()
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if layer_id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound
        areas_ui = file_study.tree.get(["input", "areas", ",".join(file_study.config.areas), "ui"])
        # standardizes 'areas_ui' to a dictionary format even if only one area exists.
        cfg_areas = list(file_study.config.areas)
        if len(cfg_areas) == 1:
            areas_ui = {cfg_areas[0]: areas_ui}

        existing_areas = [
            area for area in areas_ui if "ui" in areas_ui[area] and layer_id in _get_area_layers(areas_ui, area)
        ]
        to_remove_areas = [area for area in existing_areas if area not in areas]
        to_add_areas = [area for area in areas if area not in existing_areas]
        commands: List[ICommand] = []

        def create_update_commands(area_id: str) -> List[ICommand]:
            return [
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerX",
                    data=areas_ui[area_id]["layerX"],
                    command_context=self._command_context,
                    study_version=study.version,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerY",
                    data=areas_ui[area_id]["layerY"],
                    command_context=self._command_context,
                    study_version=study.version,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/layers",
                    data=areas_ui[area_id]["ui"]["layers"],
                    command_context=self._command_context,
                    study_version=study.version,
                ),
            ]

        for area in to_remove_areas:
            area_to_remove_layers: List[str] = _get_area_layers(areas_ui, area)
            if layer_id in areas_ui[area]["layerX"]:
                del areas_ui[area]["layerX"][layer_id]
            if layer_id in areas_ui[area]["layerY"]:
                del areas_ui[area]["layerY"][layer_id]
            if layer_id in area_to_remove_layers:
                areas_ui[area]["ui"]["layers"] = " ".join(
                    [area_layer for area_layer in area_to_remove_layers if area_layer != layer_id]
                )
            commands.extend(create_update_commands(area))
        for area in to_add_areas:
            area_to_add_layers: List[str] = _get_area_layers(areas_ui, area)
            if layer_id not in areas_ui[area]["layerX"]:
                areas_ui[area]["layerX"][layer_id] = areas_ui[area]["ui"]["x"]
            if layer_id not in areas_ui[area]["layerY"]:
                areas_ui[area]["layerY"][layer_id] = areas_ui[area]["ui"]["y"]
            if layer_id not in area_to_add_layers:
                areas_ui[area]["ui"]["layers"] = " ".join(area_to_add_layers + [layer_id])
            commands.extend(create_update_commands(area))

        study.add_commands(commands)

    def create_area(self, study: StudyInterface, area_creation_info: AreaCreation) -> Area:
        file_study = study.get_files()

        # check if area already exists
        area_id = transform_name_to_id(area_creation_info.name)
        if area_id in set(file_study.config.areas):
            raise DuplicateAreaName(area_creation_info.name)

        # Create area and apply changes in the study
        command = CreateArea(
            area_name=area_creation_info.name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return Area(
            id=area_id,
            name=area_creation_info.name,
            # this should always be empty since it's a new area
            thermals=[],
        )

    def update_area_ui(self, study: StudyInterface, area_id: str, area_ui: UpdateAreaUi, layer: str) -> None:
        command = UpdateAreaUI(
            area_id=area_id,
            area_ui=area_ui,
            layer=layer,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

    def delete_area(self, study: StudyInterface, area_id: str) -> None:
        command = RemoveArea(
            id=area_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    @staticmethod
    def _get_clusters(file_study: FileStudy, area: str) -> List[ThermalCluster]:
        thermal_clusters_data = file_study.tree.get(["input", "thermal", "clusters", area, "list"])
        result = []
        for tid, obj in thermal_clusters_data.items():
            cluster_info = parse_thermal_cluster(file_study.config.version, obj)
            result.append(cluster_info)
        return result
