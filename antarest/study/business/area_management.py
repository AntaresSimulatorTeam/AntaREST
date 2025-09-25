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
from typing import Any, Dict, List, Mapping, Optional

from antarest.core.exceptions import ConfigFileNotFound, DuplicateAreaName, LayerNotFound
from antarest.core.model import JSON
from antarest.study.business.areas.area_utils import _get_area_layers, _get_ui_info_map
from antarest.study.business.model.area_model import (
    AreaCreationDTO,
    AreaInfoDTO,
    AreaOutput,
    AreaType,
    UpdateAreaUi,
)
from antarest.study.business.model.area_properties_model import (
    AreaPropertiesUpdate,
)
from antarest.study.business.model.district_model import District
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AreaFolder,
    ThermalAreasProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_areas_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


_ALL_AREAS_PATH = "input/areas"
_THERMAL_AREAS_PATH = "input/thermal/areas"


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

    # noinspection SpellCheckingInspection
    def get_all_area_props(self, study: StudyInterface) -> Mapping[str, AreaOutput]:
        """
        Retrieves all areas of a study.

        Args:
            study: The raw study object.
        Returns:
            A mapping of area IDs to area properties.
        Raises:
            ConfigFileNotFound: if a configuration file is not found.
        """
        file_study = study.get_files()

        # Get the area information from the `/input/areas/<area>` file.
        path = _ALL_AREAS_PATH
        try:
            areas_cfg = file_study.tree.get(path.split("/"), depth=5)
        except KeyError:
            raise ConfigFileNotFound(path) from None
        else:
            # "list" and "sets" must be removed: we only need areas.
            areas_cfg.pop("list", None)
            areas_cfg.pop("sets", None)

        # Get the unserverd and spilled energy costs from the `/input/thermal/areas.ini` file.
        path = _THERMAL_AREAS_PATH
        try:
            thermal_cfg = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ConfigFileNotFound(path) from None
        else:
            thermal_areas = ThermalAreasProperties(**thermal_cfg)

        # areas_cfg contains a dictionary where the keys are the area IDs,
        # and the values are objects that can be converted to `AreaFolder`.
        area_map = {}
        for area_id, area_cfg in areas_cfg.items():
            area_folder = AreaFolder(**area_cfg)
            area_map[area_id] = AreaOutput.from_model(
                area_folder,
                average_unsupplied_energy_cost=thermal_areas.unserverd_energy_cost.get(area_id, 0.0),
                average_spilled_energy_cost=thermal_areas.spilled_energy_cost.get(area_id, 0.0),
            )

        return area_map

    # noinspection SpellCheckingInspection
    def update_areas_props(
        self, study: StudyInterface, properties: Mapping[str, AreaOutput]
    ) -> Mapping[str, AreaOutput]:
        """
        Update the properties of ares.

        Args:
            study: The raw study object.
            properties: A mapping of area IDs to area properties.

        Returns:
            A mapping of ALL area IDs to area properties.
        """
        old_areas_by_ids = self.get_all_area_props(study)
        new_areas_by_ids = dict(old_areas_by_ids)

        areas_properties: Dict[str, AreaPropertiesUpdate] = {}

        for area_id, update_area in properties.items():
            old_area = old_areas_by_ids[area_id]
            new_area = old_area.model_copy(update=update_area.model_dump(exclude_none=True))
            new_areas_by_ids[area_id] = new_area

            properties = update_area.model_dump(exclude_none=True, exclude_unset=True, by_alias=True)
            area_properties = AreaPropertiesUpdate(**properties)
            areas_properties.update({area_id: area_properties})

        command = UpdateAreasProperties(
            properties=areas_properties,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        return new_areas_by_ids

    @staticmethod
    def get_table_schema() -> JSON:
        return AreaOutput.model_json_schema()

    def get_all_areas(self, study: StudyInterface, area_type: Optional[AreaType] = None) -> List[AreaInfoDTO]:
        """
        Retrieves all areas and districts of a raw study based on the area type.

        Args:
            study: The raw study object.
            area_type: The type of area. Retrieves areas and districts if `None`.

        Returns:
            A list of area/district information.
        """
        file_study = study.get_files()
        cfg_areas: Dict[str, Area] = file_study.config.areas
        result: List[AreaInfoDTO] = []

        if area_type is None or area_type == AreaType.AREA:
            result.extend(
                AreaInfoDTO(
                    id=area_id,
                    name=area.name,
                    type=AreaType.AREA,
                    thermals=self._get_clusters(file_study, area_id),
                )
                for area_id, area in cfg_areas.items()
            )

        if area_type is None or area_type == AreaType.DISTRICT:
            cfg_sets: Dict[str, District] = file_study.config.sets
            result.extend(
                AreaInfoDTO(
                    id=set_id,
                    name=district.name or set_id,
                    type=AreaType.DISTRICT,
                    set=district.to_dto(list(cfg_areas)).areas,
                )
                for set_id, district in cfg_sets.items()
            )

        return result

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

    def create_area(self, study: StudyInterface, area_creation_info: AreaCreationDTO) -> AreaInfoDTO:
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

        return AreaInfoDTO(
            id=area_id,
            name=area_creation_info.name,
            type=AreaType.AREA,
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
