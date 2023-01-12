from typing import List, Optional

from pydantic import BaseModel

from antarest.core.exceptions import (
    AreaNotFound,
    DistrictAlreadyExist,
    DistrictNotFound,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)


class DistrictDTO(BaseModel):
    id: str
    name: str
    areas: List[str]
    output: bool
    comments: str = ""


class DistrictManager:
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_districts(self, study: Study) -> List[DistrictDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        all_areas = list(file_study.config.areas.keys())
        return [
            DistrictDTO(
                id=district_id,
                name=district.name,
                areas=district.get_areas(all_areas),
                output=district.output,
                comments=file_study.tree.get(
                    ["input", "areas", "sets", district_id]
                ).get("comments", ""),
            )
            for district_id, district in file_study.config.sets.items()
        ]

    def create_district(
        self,
        study: Study,
        name: str,
        output: bool,
        comments: str,
        areas: Optional[List[str]] = None,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        district_id = transform_name_to_id(name)
        if district_id in file_study.config.sets:
            raise DistrictAlreadyExist(district_id)
        areas = frozenset(areas or [])
        all_areas = frozenset(file_study.config.areas)
        invalid_areas = areas - all_areas
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)
        command = CreateDistrict(
            name=name,
            output=output,
            comments=comments,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=areas,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def update_district(
        self,
        study: Study,
        district_id: str,
        output: bool,
        comments: str,
        areas: Optional[List[str]] = None,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        areas = frozenset(areas or [])
        all_areas = frozenset(file_study.config.areas)
        invalid_areas = areas - all_areas
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)
        command = UpdateDistrict(
            id=district_id,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=areas,
            output=output,
            comments=comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def remove_district(self) -> None:
        pass
