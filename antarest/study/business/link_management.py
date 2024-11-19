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

from antarest.core.exceptions import ConfigFileNotFound, LinkValidationError
from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.model.link_model import LinkDTO, LinkInternal
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.config.links import LinkProperties
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink

_ALL_LINKS_PATH = "input/links"


@all_optional_model
@camel_case_model
class LinkOutput(LinkProperties):
    """
    DTO object use to get the link information.
    """


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: Study) -> t.List[LinkDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result: t.List[LinkDTO] = []

        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])

            for link in area.links:
                link_tree_config: t.Dict[str, t.Any] = links_config[link]
                link_tree_config.update({"area1": area_id, "area2": link})

                link_internal = LinkInternal.model_validate(link_tree_config)

                result.append(link_internal.to_dto())

        return result

    def create_link(self, study: Study, link_creation_dto: LinkDTO) -> LinkDTO:
        link = link_creation_dto.to_internal(StudyVersion.parse(study.version))

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(exclude_none=True),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return link_creation_dto

    def update_link(self, study: RawStudy, link_dto: LinkDTO) -> LinkDTO:
        link = link_dto.to_internal(StudyVersion.parse(study.version))
        file_study = self.storage_service.get_storage(study).get_raw(study)

        self.check_link_existence(file_study, link)

        command = UpdateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(
                include=link_dto.model_fields_set, exclude={"area1", "area2"}, exclude_none=True
            ),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        updated_link = self.get_ini_link(study, link)

        return updated_link.to_dto()

    def check_link_existence(self, file_study: FileStudy, link: LinkInternal) -> None:
        area_from, area_to = sorted([link.area1, link.area2])
        try:
            file_study.tree.get(["input", "links", area_from, "properties", area_to])
        except KeyError:
            raise LinkValidationError(f"The link {area_from} -> {area_to} is not present in the study")

    def get_ini_link(self, study: RawStudy, link: LinkInternal) -> LinkInternal:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        area_from, area_to = sorted([link.area1, link.area2])
        try:
            link_properties = file_study.tree.get(["input", "links", area_from, "properties", area_to])
        except KeyError:
            raise LinkValidationError(f"The link {area_from} -> {area_to} is not present in the study")

        link_properties.update({"area1": area_from, "area2": area_to})
        updated_link = LinkInternal.model_validate(link_properties)

        return link.model_copy(update=updated_link.model_dump())

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
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
                links_by_ids[(area1_id, area2_id)] = LinkOutput(**properties.model_dump(mode="json", by_alias=False))

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
            new_link_dto = old_link_dto.copy(
                update=update_link_dto.model_dump(mode="json", by_alias=False, exclude_none=True)
            )
            new_links_by_ids[(area1, area2)] = new_link_dto

            # Convert the DTO to a configuration object and update the configuration file.
            properties = LinkProperties(**new_link_dto.model_dump(by_alias=False))
            path = f"{_ALL_LINKS_PATH}/{area1}/properties/{area2}"
            cmd = UpdateConfig(
                target=path,
                data=properties.to_config(),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
                study_version=file_study.config.version,
            )
            commands.append(cmd)

        execute_or_add_commands(study, file_study, commands, self.storage_service)
        return new_links_by_ids

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkOutput.schema()
