from typing import List, Optional, Dict, Any

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


class LinkUIDTO(BaseModel):
    color: str
    width: float
    style: str


class LinkInfoDTO(BaseModel):
    area1: str
    area2: str
    ui: Optional[LinkUIDTO] = None


class GenericElement(BaseModel):
    id: str
    name: str


class GenericItem(BaseModel):
    element: GenericElement
    item_list: List[GenericElement]


class AllCLustersAndLinks(BaseModel):
    links: List[GenericItem]
    clusters: List[GenericItem]


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(
            self, study: Study, with_ui: bool = False
    ) -> List[LinkInfoDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result = []
        for area_id, area in file_study.config.areas.items():
            links_config: Optional[Dict[str, Any]] = None
            if with_ui:
                links_config = file_study.tree.get(
                    ["input", "links", area_id, "properties"]
                )
            for link in area.links:
                ui_info: Optional[LinkUIDTO] = None
                if with_ui and links_config and link in links_config:
                    ui_info = LinkUIDTO(
                        color=f"{links_config[link].get('colorr', '163')},{links_config[link].get('colorg', '163')},{links_config[link].get('colorb', '163')}",
                        width=links_config[link].get("link-width", 1),
                        style=links_config[link].get("link-style", "plain"),
                    )
                result.append(
                    LinkInfoDTO(area1=area_id, area2=link, ui=ui_info)
                )

        return result

    def get_clusters_and_links(self, study: Study) -> AllCLustersAndLinks:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        cluster_result = []
        link_result = []
        for area_id, area in file_study.config.areas.items():
            element: GenericElement = GenericElement(id=area_id, name=area.name)
            cluster_item_list: List[GenericElement] = []
            link_item_list: List[GenericElement] = []

            for thermal in area.thermals:
                cluster_element = GenericElement(id=thermal.id, name=thermal.name)
                cluster_item_list.append(
                    cluster_element
                )
            for link in area.links:
                link_element = GenericElement(id=link, name=file_study.config.areas[link].name)
                link_item_list.append(
                    link_element
                )
            if len(cluster_item_list) > 0:
                cluster_result.append(GenericItem(element=element, item_list=cluster_item_list))
            if len(link_item_list) > 0:
                link_result.append(GenericItem(element=element, item_list=link_item_list))

        return AllCLustersAndLinks(links=link_result, clusters=cluster_result)

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
