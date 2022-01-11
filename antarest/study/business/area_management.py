from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel

from antarest.study.model import (
    RawStudy,
    PatchArea,
    Patch,
    PatchCluster,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    Set,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService


class AreaType(Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class AreaCreationDTO(BaseModel):
    name: str
    type: AreaType
    metadata: Optional[Dict[str, Optional[str]]]
    set: Optional[List[str]]


class AreaPatchUpdateDTO(BaseModel):
    type: AreaType
    name: Optional[str]
    metadata: Optional[PatchArea]
    set: Optional[List[str]]


class ClusterInfoDTO(PatchCluster):
    id: str
    name: str
    unitcount: int
    nominalcapacity: int
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


class AreaManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service
        self.patch_service = PatchService()

    def get_all_areas(
        self, study: RawStudy, area_type: Optional[AreaType] = None
    ) -> List[AreaInfoDTO]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        metadata = self.patch_service.get(study)
        areas_metadata: Dict[str, PatchArea] = metadata.areas or {}
        result = []
        if area_type is None or area_type == AreaType.AREA:
            for area_name, area in file_study.config.areas.items():
                result.append(
                    AreaInfoDTO(
                        id=area_name,
                        name=area.name,
                        type=AreaType.AREA,
                        metadata=areas_metadata.get(area_name, PatchArea()),
                        thermals=self._get_clusters(
                            file_study, area_name, metadata
                        ),
                    )
                )

        if area_type is None or area_type == AreaType.DISTRICT:
            for set_name in file_study.config.sets:
                result.append(
                    AreaInfoDTO(
                        id=set_name,
                        name=file_study.config.sets[set_name].name or set_name,
                        type=AreaType.DISTRICT,
                        set=file_study.config.sets[set_name].get_areas(
                            list(file_study.config.areas.keys())
                        ),
                        metadata=areas_metadata.get(set_name, PatchArea()),
                    )
                )

        return result

    def create_area(
        self, study: RawStudy, area_creation_info: AreaCreationDTO
    ) -> AreaInfoDTO:
        raise NotImplementedError()

    def update_area(
        self,
        study: RawStudy,
        area_id: str,
        area_creation_info: AreaPatchUpdateDTO,
    ) -> AreaInfoDTO:
        if area_creation_info.metadata:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            area_or_set = file_study.config.areas.get(
                area_id
            ) or file_study.config.sets.get(area_id)
            patch = self.patch_service.get(study)
            patch.areas = patch.areas or {}
            patch.areas[area_id] = area_creation_info.metadata
            self.patch_service.save(study, patch)
            return AreaInfoDTO(
                id=area_id,
                name=area_or_set.name if area_or_set is not None else area_id,
                type=AreaType.AREA
                if isinstance(area_or_set, Area)
                else AreaType.DISTRICT,
                metadata=patch.areas.get(area_id),
                set=area_or_set.get_areas(list(file_study.config.areas.keys()))
                if isinstance(area_or_set, Set)
                else [],
            )
        raise NotImplementedError()

    def update_thermal_cluster_metadata(
        self,
        study: RawStudy,
        area_id: str,
        clusters_metadata: Dict[str, PatchCluster],
    ) -> AreaInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        patch = self.patch_service.get(study)
        patch.areas = patch.areas or {}
        patch.thermal_clusters = patch.thermal_clusters or {}
        patch.thermal_clusters.update(
            {
                f"{area_id}.{tid}": clusters_metadata[tid]
                for tid in clusters_metadata
            }
        )
        self.patch_service.save(study, patch)
        return AreaInfoDTO(
            id=area_id,
            name=file_study.config.areas[area_id].name,
            type=AreaType.AREA,
            metadata=patch.areas.get(area_id, PatchArea()).dict(),
            thermals=self._get_clusters(file_study, area_id, patch),
            set=None,
        )

    def delete_area(self, study: RawStudy, area_id: str) -> None:
        raise NotImplementedError()

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

    def _get_clusters(
        self, file_study: FileStudy, area: str, metadata_patch: Patch
    ) -> List[ClusterInfoDTO]:
        thermal_clusters_data = file_study.tree.get(
            ["input", "thermal", "clusters", area, "list"]
        )
        cluster_patch = metadata_patch.thermal_clusters or {}
        return [
            AreaManager._update_with_cluster_metadata(
                area,
                ClusterInfoDTO.parse_obj(
                    {**thermal_clusters_data[tid], "id": tid}
                ),
                cluster_patch,
            )
            for tid in thermal_clusters_data
        ]
