# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import typing as t

from antares.study.version import StudyVersion
from pydantic import ConfigDict

from antarest.core.exceptions import ConfigFileNotFound, LinkValidationError
from antarest.core.model import JSON
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import STUDY_VERSION_8_2, RawStudy
from antarest.study.storage.rawstudy.model.filesystem.config.links import LinkProperties
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import (
    AreaInfo,
    CreateLink,
    LinkInfoProperties,
    LinkInfoProperties820,
)
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink

_ALL_LINKS_PATH = "input/links"


class LinkInfoDTOBase(AreaInfo, LinkInfoProperties):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")


class LinkInfoDTO820(AreaInfo, LinkInfoProperties820):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")


LinkInfoDTO = t.Union[LinkInfoDTO820, LinkInfoDTOBase]


@all_optional_model
@camel_case_model
class LinkOutput(LinkProperties):
    """
    DTO object use to get the link information.
    """


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: RawStudy) -> t.List[LinkInfoDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result: t.List[LinkInfoDTO] = []

        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])

            for link in area.links:
                link_tree_config: t.Dict[str, t.Any] = links_config[link]
                link_tree_config.update({"area1": area_id, "area2": link})

                link_properties = {"area1": area_id, "area2": link}
                link_dto: LinkInfoDTO
                if StudyVersion.parse(study.version) < STUDY_VERSION_8_2:
                    link_properties.update(LinkInfoProperties(**link_tree_config).model_dump())
                    link_dto = LinkInfoDTOBase(**link_properties)
                else:
                    link_properties.update(LinkInfoProperties820(**link_tree_config).model_dump())
                    link_dto = LinkInfoDTO820(**link_properties)

                result.append(link_dto)

        return result

    def create_link(self, study: RawStudy, link_creation_info: LinkInfoDTO) -> LinkInfoDTO:
        if link_creation_info.area1 == link_creation_info.area2:
            raise LinkValidationError(f"Cannot create link on same area: {link_creation_info.area1}")

        link_dto: LinkInfoDTO
        if StudyVersion.parse(study.version) >= STUDY_VERSION_8_2:
            link_dto = LinkInfoDTO820.model_validate(link_creation_info.model_dump())
        else:
            forbidden_fields = {"filter_synthesis", "filter_year_by_year"}
            fields = set(link_creation_info.model_dump(exclude_defaults=True))
            if forbidden_fields & fields:
                raise LinkValidationError("Cannot specify a filter value for study's version earlier than v8.2")
            link_dto = LinkInfoDTOBase.model_validate(link_creation_info.model_dump(exclude=forbidden_fields))

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link_creation_info.area1,
            area2=link_creation_info.area2,
            parameters=link_dto.model_dump(exclude_none=True),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return link_dto

    def update_link(self, study: RawStudy, link_update_info: LinkInfoDTO) -> LinkInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        self.check_attributes_coherence(file_study, StudyVersion.parse(study.version), link_update_info)

        command = UpdateLink(
            area1=link_update_info.area1,
            area2=link_update_info.area2,
            parameters=link_update_info.model_dump(
                mode="json", exclude={"area1", "area2"}, exclude_none=True, exclude_unset=True
            ),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        updated_link = self.get_one_link(study, link_update_info)
        return updated_link

    def check_attributes_coherence(
        self, file_study: FileStudy, study_version: StudyVersion, link_creation_info: LinkInfoDTO
    ) -> None:
        if link_creation_info.area1 == link_creation_info.area2:
            raise LinkValidationError("Area 1 and Area 2 can not be the same")

        area_from, area_to = sorted([link_creation_info.area1, link_creation_info.area2])
        try:
            file_study.tree.get(["input", "links", area_from, "properties", area_to])
        except KeyError:
            raise LinkValidationError(f"The link {area_from} -> {area_to} is not present in the study")

        if study_version < STUDY_VERSION_8_2:
            if isinstance(link_creation_info, LinkInfoDTO820):
                if (
                    link_creation_info.filter_synthesis is not None
                    or link_creation_info.filter_year_by_year is not None
                ):
                    raise LinkValidationError("Cannot specify a filter value for study's version earlier than v8.2")

    def get_one_link(self, study: RawStudy, link_creation_info: LinkInfoDTO) -> LinkInfoDTO:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        area_from, area_to = sorted([link_creation_info.area1, link_creation_info.area2])
        try:
            link_updated = LinkInfoProperties.model_validate(
                file_study.tree.get(["input", "links", area_from, "properties", area_to])
            )
        except KeyError:
            raise LinkValidationError(f"The link {area_from} -> {area_to} is not present in the study")

        return link_creation_info.model_copy(update=link_updated.model_dump())

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
            updated_link_properties = old_link_dto.copy(
                update=update_link_dto.model_dump(by_alias=False, exclude_none=True)
            )
            new_links_by_ids[(area1, area2)] = updated_link_properties

            # Convert the DTO to a configuration object and update the configuration file.
            properties = LinkProperties(**updated_link_properties.model_dump(by_alias=False))
            path = f"{_ALL_LINKS_PATH}/{area1}/properties/{area2}"
            cmd = UpdateConfig(
                target=path,
                data=properties.to_ini(int(study.version)),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
            commands.append(cmd)

        execute_or_add_commands(study, file_study, commands, self.storage_service)
        return new_links_by_ids

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkOutput.schema()
