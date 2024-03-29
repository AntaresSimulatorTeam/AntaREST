import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel

from antarest.core.exceptions import DuplicateAreaName, LayerNotAllowedToBeDeleted, LayerNotFound
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Patch, PatchArea, PatchCluster, RawStudy, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, DistrictSet, transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

logger = logging.getLogger(__name__)


class AreaType(Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class AreaCreationDTO(BaseModel):
    name: str
    type: AreaType
    metadata: Optional[PatchArea]
    set: Optional[List[str]]


class ClusterInfoDTO(PatchCluster):
    id: str
    name: str
    enabled: bool = True
    unitcount: int = 0
    nominalcapacity: int = 0
    group: Optional[str] = None
    min_stable_power: Optional[int] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    spinning: Optional[float] = None
    marginal_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    market_bid_cost: Optional[float] = None


class AreaInfoDTO(AreaCreationDTO):
    id: str
    thermals: Optional[List[ClusterInfoDTO]] = None


class AreaUI(BaseModel):
    x: int
    y: int
    color_rgb: Tuple[int, int, int]


class LayerInfoDTO(BaseModel):
    id: str
    name: str
    areas: List[str]


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
    return ui_info_map


def _get_area_layers(area_uis: Dict[str, Any], area: str) -> List[str]:
    if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
        return re.split(r"\s+", (str(area_uis[area]["ui"]["layers"]) or ""))
    return []


class AreaManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
        repository: StudyMetadataRepository,
    ) -> None:
        self.storage_service = storage_service
        self.patch_service = PatchService(repository=repository)

    def get_all_areas(self, study: RawStudy, area_type: Optional[AreaType] = None) -> List[AreaInfoDTO]:
        """
        Retrieves all areas and districts of a raw study based on the area type.

        Args:
            study: The raw study object.
            area_type: The type of area. Retrieves areas and districts if `None`.

        Returns:
            A list of area/district information.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        metadata = self.patch_service.get(study)
        areas_metadata: Dict[str, PatchArea] = metadata.areas or {}
        cfg_areas: Dict[str, Area] = file_study.config.areas
        result: List[AreaInfoDTO] = []

        if area_type is None or area_type == AreaType.AREA:
            result.extend(
                AreaInfoDTO(
                    id=area_id,
                    name=area.name,
                    type=AreaType.AREA,
                    metadata=areas_metadata.get(area_id, PatchArea()),
                    thermals=self._get_clusters(file_study, area_id, metadata),
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
                    metadata=areas_metadata.get(set_id, PatchArea()),
                )
                for set_id, district in cfg_sets.items()
            )

        return result

    def get_all_areas_ui_info(self, study: RawStudy) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Args:
            study: The raw study object containing the study's data.

        Returns:
            A dictionary containing information about the user interface for the areas.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        area_ids = list(file_study.config.areas)
        return _get_ui_info_map(file_study, area_ids)

    def get_layers(self, study: RawStudy) -> List[LayerInfoDTO]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
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

    def update_layer_areas(self, study: RawStudy, layer_id: str, areas: List[str]) -> None:
        logger.info(f"Updating layer {layer_id} with areas {areas}")
        file_study = self.storage_service.get_storage(study).get_raw(study)
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
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerY",
                    data=areas_ui[area_id]["layerY"],
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/layers",
                    data=areas_ui[area_id]["ui"]["layers"],
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
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

        execute_or_add_commands(study, file_study, commands, self.storage_service)

    def update_layer_name(self, study: RawStudy, layer_id: str, layer_name: str) -> None:
        logger.info(f"Updating layer {layer_id} with name {layer_name}")
        file_study = self.storage_service.get_storage(study).get_raw(study)
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if layer_id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound
        command = UpdateConfig(
            target=f"layers/layers/layers/{layer_id}",
            data=layer_name,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def create_layer(self, study: RawStudy, layer_name: str) -> str:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        layers = file_study.tree.get(["layers", "layers", "layers"])
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        new_id = max((int(layer) for layer in layers), default=0) + 1
        if new_id == 1:
            command = UpdateConfig(
                target="layers/layers/layers",
                data={"0": "All", "1": layer_name},
                command_context=command_context,
            )
        else:
            command = UpdateConfig(
                target=f"layers/layers/layers/{new_id}",
                data=layer_name,
                command_context=command_context,
            )
        execute_or_add_commands(study, file_study, [command], self.storage_service)
        return str(new_id)

    def remove_layer(self, study: RawStudy, layer_id: str) -> None:
        """
        Remove a layer from a study.

        Raises:
            LayerNotAllowedToBeDeleted: If the layer ID is "0".
            LayerNotFound: If the layer ID is not found.
        """
        if layer_id == "0":
            raise LayerNotAllowedToBeDeleted

        file_study = self.storage_service.get_storage(study).get_raw(study)
        layers = file_study.tree.get(["layers", "layers", "layers"])

        if layer_id not in layers:
            raise LayerNotFound

        del layers[layer_id]

        command = UpdateConfig(
            target="layers/layers/layers",
            data=layers,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def create_area(self, study: Study, area_creation_info: AreaCreationDTO) -> AreaInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # check if area already exists
        area_id = transform_name_to_id(area_creation_info.name)
        if area_id in set(file_study.config.areas):
            raise DuplicateAreaName(area_creation_info.name)

        # Create area and apply changes in the study
        command = CreateArea(
            area_name=area_creation_info.name,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Update metadata
        patch = self.patch_service.get(study)
        patch.areas = patch.areas or {}
        patch.areas[area_id] = area_creation_info.metadata or PatchArea()
        self.patch_service.save(study, patch)
        return AreaInfoDTO(
            id=area_id,
            name=area_creation_info.name,
            type=AreaType.AREA,
            # this should always be empty since it's a new area
            thermals=[],
            metadata=area_creation_info.metadata,
        )

    def update_area_metadata(
        self,
        study: Study,
        area_id: str,
        area_metadata: PatchArea,
    ) -> AreaInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        area_or_set = file_study.config.areas.get(area_id) or file_study.config.sets.get(area_id)
        patch = self.patch_service.get(study)
        patch.areas = patch.areas or {}
        patch.areas[area_id] = area_metadata
        self.patch_service.save(study, patch)
        return AreaInfoDTO(
            id=area_id,
            name=area_or_set.name if area_or_set is not None else area_id,
            type=AreaType.AREA if isinstance(area_or_set, Area) else AreaType.DISTRICT,
            metadata=patch.areas.get(area_id),
            set=area_or_set.get_areas(list(file_study.config.areas)) if isinstance(area_or_set, DistrictSet) else [],
        )

    def update_area_ui(self, study: Study, area_id: str, area_ui: AreaUI, layer: str = "0") -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        commands = (
            [
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/x",
                    data=area_ui.x,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/y",
                    data=area_ui.y,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/color_r",
                    data=area_ui.color_rgb[0],
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/color_g",
                    data=area_ui.color_rgb[1],
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/ui/color_b",
                    data=area_ui.color_rgb[2],
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
            ]
            if layer == "0"
            else []
        )
        commands.extend(
            [
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerX/{layer}",
                    data=area_ui.x,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerY/{layer}",
                    data=area_ui.y,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui/layerColor/{layer}",
                    data=f"{str(area_ui.color_rgb[0])} , {str(area_ui.color_rgb[1])} , {str(area_ui.color_rgb[2])}",
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                ),
            ]
        )
        execute_or_add_commands(study, file_study, commands, self.storage_service)

    def update_thermal_cluster_metadata(
        self,
        study: Study,
        area_id: str,
        clusters_metadata: Dict[str, PatchCluster],
    ) -> AreaInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        patch = self.patch_service.get(study)
        patch.areas = patch.areas or {}
        patch.thermal_clusters = patch.thermal_clusters or {}
        patch.thermal_clusters.update({f"{area_id}.{tid}": clusters_metadata[tid] for tid in clusters_metadata})
        self.patch_service.save(study, patch)
        return AreaInfoDTO(
            id=area_id,
            name=file_study.config.areas[area_id].name,
            type=AreaType.AREA,
            metadata=patch.areas.get(area_id, PatchArea()).dict(),
            thermals=self._get_clusters(file_study, area_id, patch),
            set=None,
        )

    def delete_area(self, study: Study, area_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveArea(
            id=area_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    @staticmethod
    def _update_with_cluster_metadata(
        area: str,
        info: ClusterInfoDTO,
        cluster_patch: Dict[str, PatchCluster],
    ) -> ClusterInfoDTO:
        patch = cluster_patch.get(f"{area}.{info.id}", PatchCluster())
        info.code_oi = patch.code_oi
        info.type = patch.type
        return info

    @staticmethod
    def _get_clusters(file_study: FileStudy, area: str, metadata_patch: Patch) -> List[ClusterInfoDTO]:
        thermal_clusters_data = file_study.tree.get(["input", "thermal", "clusters", area, "list"])
        cluster_patch = metadata_patch.thermal_clusters or {}
        return [
            AreaManager._update_with_cluster_metadata(
                area,
                ClusterInfoDTO.parse_obj({**thermal_clusters_data[tid], "id": tid}),
                cluster_patch,
            )
            for tid in thermal_clusters_data
        ]
