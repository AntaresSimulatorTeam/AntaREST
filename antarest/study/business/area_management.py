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
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, TypeVar

from antarest.core.exceptions import ConfigFileNotFound, DuplicateAreaName, LayerNotAllowedToBeDeleted, LayerNotFound
from antarest.core.model import JSON
from antarest.study.business.areas.thermal_management import ThermalClusterOutput, create_thermal_output
from antarest.study.business.model.area_model import (
    AreaCreationDTO,
    AreaInfoDTO,
    AreaOutput,
    AreaType,
    LayerInfoDTO,
    UpdateAreaUi,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AreaFolder,
    ThermalAreasProperties,
    UIProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, DistrictSet
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.update_area_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


_ALL_AREAS_PATH = "input/areas"
_THERMAL_AREAS_PATH = "input/thermal/areas"
T = TypeVar("T")


def _get_ui_info_map(file_study: FileStudy, area_ids: Sequence[str]) -> Dict[str, Any]:
    """
    Get the UI information (a JSON object) for each selected Area.

    Args:
        file_study: A file study from which the configuration can be read.
        area_ids: List of selected area IDs.

    Returns:
        Dictionary where keys are IDs, and values are UI objects.

    Raises:
        ChildNotFoundError: if one of the Area IDs is not found in the configuration.
    """
    # If there is no ID, it is better to return an empty dictionary
    # instead of raising an obscure exception.
    if not area_ids:
        return {}

    ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

    # If there is only one ID in the `area_ids`, the result returned from
    # the `file_study.tree.get` call will be a single UI object.
    # On the other hand, if there are multiple values in `area_ids`,
    # the result will be a dictionary where the keys are the IDs,
    # and the values are the corresponding UI objects.
    if len(area_ids) == 1:
        ui_info_map = {area_ids[0]: ui_info_map}

    # Convert to UIProperties to ensure that the UI object is valid.
    ui_info_map = {area_id: UIProperties(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

    return ui_info_map


def _get_area_layers(area_uis: Dict[str, Any], area: str) -> List[str]:
    if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
        return re.split(r"\s+", (str(area_uis[area]["ui"]["layers"]) or ""))
    return []


def pick_value(
    old: Optional[T], new: Optional[T], condition: Callable[[Optional[T]], bool] = lambda x: True
) -> Optional[T]:
    return new if (old != new and condition(new)) else old


def update_area_folder_configuration(old_area: AreaOutput, new_area: AreaOutput) -> AreaFolder:
    optimization = pick_value(old_area.area_folder.optimization, new_area.area_folder.optimization)
    adequacy_patch = pick_value(
        old_area.area_folder.adequacy_patch, new_area.area_folder.adequacy_patch, lambda x: bool(x)
    )
    return AreaFolder(adequacy_patch=adequacy_patch, optimization=optimization)


def update_thermal_configuration(area_id: str, old_area: AreaOutput, new_area: AreaOutput) -> ThermalAreasProperties:
    average_unsupplied_energy_cost = pick_value(
        old_area.average_unsupplied_energy_cost, new_area.average_unsupplied_energy_cost
    )
    average_spilled_energy_cost = pick_value(old_area.average_spilled_energy_cost, new_area.average_spilled_energy_cost)
    return ThermalAreasProperties(
        # type: ignore[call-arg]
        unserverdenergycost={area_id: average_unsupplied_energy_cost},
        spilledenergycost={area_id: average_spilled_energy_cost},
    )


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
        self, study: StudyInterface, update_areas_by_ids: Mapping[str, AreaOutput]
    ) -> Mapping[str, AreaOutput]:
        """
        Update the properties of ares.

        Args:
            study: The raw study object.
            update_areas_by_ids: A mapping of area IDs to area properties.

        Returns:
            A mapping of ALL area IDs to area properties.
        """
        old_areas_by_ids = self.get_all_area_props(study)
        new_areas_by_ids = dict(old_areas_by_ids)

        dict_areas_folder: Dict[str, AreaFolder] = {}
        list_thermal_areas_properties: List[ThermalAreasProperties] = []

        for area_id, update_area in update_areas_by_ids.items():
            old_area = old_areas_by_ids[area_id]
            new_area = old_area.model_copy(update=update_area.model_dump(mode="json", exclude_none=True))
            new_areas_by_ids[area_id] = new_area

            area_folder = update_area_folder_configuration(old_area, new_area)
            thermal_area_properties = update_thermal_configuration(area_id, old_area, new_area)

            dict_areas_folder[area_id] = area_folder
            list_thermal_areas_properties.append(thermal_area_properties)

        command = UpdateAreasProperties(
            dict_area_folder=dict_areas_folder,
            list_thermal_area_properties=list_thermal_areas_properties,
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
            cfg_sets: Dict[str, DistrictSet] = file_study.config.sets
            result.extend(
                AreaInfoDTO(
                    id=set_id,
                    name=district.name or set_id,
                    type=AreaType.DISTRICT,
                    set=district.get_areas(list(cfg_areas)),
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

    def get_layers(self, study: StudyInterface) -> List[LayerInfoDTO]:
        file_study = study.get_files()
        area_ids = list(file_study.config.areas)
        ui_info_map = _get_ui_info_map(file_study, area_ids)
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if not layers:
            layers["0"] = "All"
        return [
            LayerInfoDTO(
                id=str(layer),
                name=layers[str(layer)],
                areas=[
                    area
                    for area in ui_info_map
                    if str(layer) in _get_area_layers(ui_info_map, area)
                    # the layer 0 always display all areas
                    or str(layer) == "0"
                ],
            )
            for layer in layers
        ]

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

    def update_layer_name(self, study: StudyInterface, layer_id: str, layer_name: str) -> None:
        logger.info(f"Updating layer {layer_id} with name {layer_name}")
        file_study = study.get_files()
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if layer_id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound
        command = UpdateConfig(
            target=f"layers/layers/layers/{layer_id}",
            data=layer_name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def create_layer(self, study: StudyInterface, layer_name: str) -> str:
        file_study = study.get_files()
        layers = file_study.tree.get(["layers", "layers", "layers"])
        command_context = self._command_context
        new_id = max((int(layer) for layer in layers), default=0) + 1
        if new_id == 1:
            command = UpdateConfig(
                target="layers/layers/layers",
                data={"0": "All", "1": layer_name},
                command_context=command_context,
                study_version=study.version,
            )
        else:
            command = UpdateConfig(
                target=f"layers/layers/layers/{new_id}",
                data=layer_name,
                command_context=command_context,
                study_version=study.version,
            )
        study.add_commands([command])
        return str(new_id)

    def remove_layer(self, study: StudyInterface, layer_id: str) -> None:
        """
        Remove a layer from a study.

        Raises:
            LayerNotAllowedToBeDeleted: If the layer ID is "0".
            LayerNotFound: If the layer ID is not found.
        """
        if layer_id == "0":
            raise LayerNotAllowedToBeDeleted

        file_study = study.get_files()
        layers = file_study.tree.get(["layers", "layers", "layers"])

        if layer_id not in layers:
            raise LayerNotFound

        del layers[layer_id]

        command = UpdateConfig(
            target="layers/layers/layers",
            data=layers,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

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
    def _get_clusters(file_study: FileStudy, area: str) -> List[ThermalClusterOutput]:
        thermal_clusters_data = file_study.tree.get(["input", "thermal", "clusters", area, "list"])
        result = []
        for tid, obj in thermal_clusters_data.items():
            cluster_info = create_thermal_output(file_study.config.version, tid, obj)
            result.append(cluster_info)
        return result
