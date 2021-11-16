from typing import List

from pydantic import BaseModel

from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)


class LinkInfoDTO(BaseModel):
    area1: str
    area2: str


class LinkManager:
    def __init__(self, raw_study_service: RawStudyService) -> None:
        self.raw_study_service = raw_study_service

    def get_all_links(self, study: RawStudy) -> List[LinkInfoDTO]:
        file_study = self.raw_study_service.get_raw(study)
        result = []
        for area_id, area in file_study.config.areas.items():
            for link in area.links:
                result.append(LinkInfoDTO(area1=area_id, area2=link))

        return result

    def create_link(
        self, study: RawStudy, link_creation_info: LinkInfoDTO
    ) -> LinkInfoDTO:
        raise NotImplementedError()

    def delete_area(self, study: RawStudy, area1_id: str, area2_id) -> None:
        raise NotImplementedError()
