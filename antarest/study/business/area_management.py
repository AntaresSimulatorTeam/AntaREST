from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel

from antarest.study.model import RawStudy, PatchArea, PatchLeafDict
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    Set,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)


class AreaType(Enum):
    AREA = "AREA"
    CLUSTER = "CLUSTER"


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


class AreaInfoDTO(AreaCreationDTO):
    id: str


class AreaManager:
    def __init__(self, raw_study_service: RawStudyService) -> None:
        self.raw_study_service = raw_study_service

    def get_all_areas(
        self, study: RawStudy, area_type: Optional[AreaType] = None
    ) -> List[AreaInfoDTO]:
        file_study = self.raw_study_service.get_raw(study)
        metadata = self.raw_study_service.patch_service.get(study)
        areas_metadata: Dict[str, PatchArea] = metadata.areas or {}  # type: ignore
        result = []
        if area_type is None or area_type == AreaType.AREA:
            for area_name, area in file_study.config.areas.items():
                result.append(
                    AreaInfoDTO(
                        id=area_name,
                        name=area.name,
                        type=AreaType.AREA,
                        metadata=areas_metadata.get(area_name, PatchArea()),
                    )
                )

        if area_type is None or area_type == AreaType.CLUSTER:
            for set_name in file_study.config.sets:
                result.append(
                    AreaInfoDTO(
                        id=set_name,
                        name=file_study.config.sets[set_name].name or set_name,
                        type=AreaType.CLUSTER,
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
            file_study = self.raw_study_service.get_raw(study)
            area_or_set = file_study.config.areas.get(
                area_id
            ) or file_study.config.sets.get(area_id)
            patch = self.raw_study_service.patch_service.get(study)
            patch.areas = (patch.areas or PatchLeafDict()).patch(
                PatchLeafDict({area_id: area_creation_info.metadata})
            )
            self.raw_study_service.patch_service.patch(study, patch.dict())
            return AreaInfoDTO(
                id=area_id,
                name=area_or_set.name if area_or_set is not None else area_id,
                type=AreaType.AREA
                if isinstance(area_or_set, Area)
                else AreaType.CLUSTER,
                metadata=patch.areas.get(area_id),
                set=area_or_set.get_areas(list(file_study.config.areas.keys()))
                if isinstance(area_or_set, Set)
                else [],
            )
        raise NotImplementedError()

    def delete_area(self, study: RawStudy, area_id: str) -> None:
        raise NotImplementedError()
