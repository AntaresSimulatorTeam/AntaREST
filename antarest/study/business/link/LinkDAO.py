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
from abc import ABC, abstractmethod
from typing import List

from antarest.study.business.model.link_model import LinkDTO
from antarest.study.model import Study


class LinkDAO(ABC):
    """
    DAO interface for managing the links of a study.
    Provides methods to access, add, save, and delete links.
    """

    @abstractmethod
    def get_all_links(self, study: Study) -> List[LinkDTO]:
        """
        Retrieves all the links associated with a study.
        Args:
            study (Study): The study for which to retrieve the links.
        Returns:
            List[LinkInternal]: A list of links associated with the study.
        """
        pass

    @abstractmethod
    def create_link(self, study: Study, link: LinkDTO) -> LinkDTO:
        """
        Adds an individual link to a study.
        Args:
            study (Study): The target study.
            link (LinkInternal): The link to be added.
        """
        pass

    @abstractmethod
    def delete_link(self, study: Study, area1_id: str, area2_id: str) -> None:
        """
        Deletes a specific link associated with a study.

        Args:
            study (Study): The study containing the link to be deleted.
            area1_id (str): The ID of the source area of the link.
            area2_id (str): The ID of the target area of the link.
        """
        pass

