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

from antarest.core.exceptions import ConfigFileNotFound
from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.link.LinkDAO import LinkDAO
from antarest.study.business.model.link_model import LinkDTO
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.config.links import LinkProperties
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

_ALL_LINKS_PATH = "input/links"


@all_optional_model
@camel_case_model
class LinkOutput(LinkProperties):
    """
    DTO object use to get the link information.
    """


class LinkManager:
    def __init__(self, link_dao: LinkDAO) -> None:
        self.link_dao = link_dao

    def get_all_links(self, study: Study) -> t.List[LinkDTO]:
        return self.link_dao.get_all_links(study)

    def create_link(self, study: Study, link_dto: LinkDTO) -> LinkDTO:
        return self.link_dao.create_link(study, link_dto)

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        self.link_dao.delete_link(study, area1_id, area2_id)

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
