from typing import List

from pydantic import BaseModel

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)


class LinkInfoDTO(BaseModel):
    area1: str
    area2: str


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: Study) -> List[LinkInfoDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result = []
        for area_id, area in file_study.config.areas.items():
            for link in area.links:
                result.append(LinkInfoDTO(area1=area_id, area2=link))

        return result

    def create_link(
        self, study: Study, link_creation_info: LinkInfoDTO
    ) -> LinkInfoDTO:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        command = CreateLink(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
        return LinkInfoDTO(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
        )

    def delete_link(self, study: Study, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
