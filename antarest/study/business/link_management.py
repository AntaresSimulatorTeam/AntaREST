import typing as t

from pydantic import BaseModel

from antarest.core.exceptions import ConfigFileNotFound
from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.links import LinkProperties
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

_ALL_LINKS_PATH = "input/links"


class LinkUIDTO(BaseModel):
    color: str
    width: float
    style: str


class LinkInfoDTO(BaseModel):
    area1: str
    area2: str
    ui: t.Optional[LinkUIDTO] = None


@all_optional_model
@camel_case_model
class LinkOutput(LinkProperties):
    """
    DTO object use to get the link information.
    """


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: RawStudy, with_ui: bool = False) -> t.List[LinkInfoDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result = []
        for area_id, area in file_study.config.areas.items():
            links_config: t.Optional[t.Dict[str, t.Any]] = None
            if with_ui:
                links_config = file_study.tree.get(["input", "links", area_id, "properties"])
            for link in area.links:
                ui_info: t.Optional[LinkUIDTO] = None
                if with_ui and links_config and link in links_config:
                    ui_info = LinkUIDTO(
                        color=f"{links_config[link].get('colorr', '163')},{links_config[link].get('colorg', '163')},{links_config[link].get('colorb', '163')}",
                        width=links_config[link].get("link-width", 1),
                        style=links_config[link].get("link-style", "plain"),
                    )
                result.append(LinkInfoDTO(area1=area_id, area2=link, ui=ui_info))

        return result

    def create_link(self, study: RawStudy, link_creation_info: LinkInfoDTO) -> LinkInfoDTO:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        command = CreateLink(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)
        return LinkInfoDTO(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
        )

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def get_all_links_props(self, study: RawStudy) -> t.Mapping[t.Tuple[str, str], LinkOutput]:
        """
        Retrieves all links properties from the study.

        Args:
            study: The raw study object.
        Returns:
            A mapping of link IDS `(area1_id, area2_id)` to link properties.
        Raises:
            ConfigFileNotFound: if a configuration file is not found.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # Get the link information from the `input/links/{area1}/properties.ini` file.
        path = _ALL_LINKS_PATH
        try:
            links_cfg = file_study.tree.get(path.split("/"), depth=5)
        except KeyError:
            raise ConfigFileNotFound(path) from None

        # areas_cfg contains a dictionary where the keys are the area IDs,
        # and the values are objects that can be converted to `LinkFolder`.
        links_by_ids = {}
        for area1_id, entries in links_cfg.items():
            property_map = entries.get("properties") or {}
            for area2_id, properties_cfg in property_map.items():
                area1_id, area2_id = sorted([area1_id, area2_id])
                properties = LinkProperties(**properties_cfg)
                links_by_ids[(area1_id, area2_id)] = LinkOutput(**properties.model_dump(by_alias=False))

        return links_by_ids

    def update_links_props(
        self,
        study: RawStudy,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkOutput],
    ) -> t.Mapping[t.Tuple[str, str], LinkOutput]:
        old_links_by_ids = self.get_all_links_props(study)
        new_links_by_ids = {}
        file_study = self.storage_service.get_storage(study).get_raw(study)
        commands = []
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            # Update the link properties.
            old_link_dto = old_links_by_ids[(area1, area2)]
            new_link_dto = old_link_dto.copy(update=update_link_dto.model_dump(by_alias=False, exclude_none=True))
            new_links_by_ids[(area1, area2)] = new_link_dto

            # Convert the DTO to a configuration object and update the configuration file.
            properties = LinkProperties(**new_link_dto.model_dump(by_alias=False))
            path = f"{_ALL_LINKS_PATH}/{area1}/properties/{area2}"
            cmd = UpdateConfig(
                target=path,
                data=properties.to_config(),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
            commands.append(cmd)

        execute_or_add_commands(study, file_study, commands, self.storage_service)
        return new_links_by_ids

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkOutput.schema()
