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
from typing import List

from antares.study.version import StudyVersion

from antarest.study.business.link.LinkDAO import LinkDAO
from antarest.study.business.model.link_model import LinkDTO, LinkInternal
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink


class LinkFromStorageDAO(LinkDAO):
    """
    LinkFromStorageDAO is responsible for managing study links in persistent storage.
    It provides methods to retrieve, create, and delete links directly in the underlying storage.

    Attributes:
        storage_service: The service used to interact with the persistent storage.
    """

    def __init__(self, storage_service) -> None:
        """
        Initializes the LinkFromStorageDAO with a storage service.

        Args:
            storage_service: The service responsible for interacting with persistent storage.
        """
        self.storage_service = storage_service

    def get_all_links(self, study: Study) -> List[LinkDTO]:
        """
        Retrieves all links for a given study from persistent storage.

        This method reads the study configuration and retrieves all links between areas
        defined in the study.

        Args:
            study (Study): The study for which to retrieve the links.

        Returns:
            List[LinkDTO]: A list of links associated with the study.
        """
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

    def create_link(self, study: Study, link_dto: LinkDTO) -> LinkDTO:
        """
        Creates a new link for a study in persistent storage.

        This method converts the provided LinkDTO into an internal model,
        then creates a command to add the link to the study. The command is executed
        immediately or queued for later execution.

        Args:
            study (Study): The study where the link should be created.
            link_dto (LinkDTO): The link to be added.

        Returns:
            LinkDTO: The newly created link.
        """
        link = link_dto.to_internal(StudyVersion.parse(study.version))

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
        return link_dto

    def delete_link(self, study: Study, area1_id: str, area2_id: str) -> None:
        """
        Deletes a specific link from a study in persistent storage.

        This method creates a command to remove the link from the study. The command
        is executed immediately or queued for later excecution.

        Args:
            study (Study): The study containing the link to be deleted.
            area1_id (str): The ID of the source area of the link.
            area2_id (str): The ID of the target area of the link.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)
