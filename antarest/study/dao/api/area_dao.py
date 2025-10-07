# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from typing import Any, Dict, List

from antarest.study.business.model.area_model import Area


class ReadOnlyAreaDao(ABC):
    @abstractmethod
    def get_all_areas(self) -> List[Area]:
        """
        Retrieve all physical areas of a study.

        Returns:
            The list of areas with their basic information.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_area(self, area_id: str) -> Area:
        """
        Retrieve a specific area by its ID.

        Args:
            area_id: The area identifier.

        Returns:
            The area with its basic information.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        raise NotImplementedError()

    @abstractmethod
    def area_exists(self, area_id: str) -> bool:
        """
        Check if an area exists in the study.

        Args:
            area_id: The area identifier.

        Returns:
            True if the area exists, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            A dictionary containing information about the user interface for the areas.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        raise NotImplementedError()


class AreaDao(ReadOnlyAreaDao):
    """
    DAO for area operations.

    Note: Write operations (create, update, delete) are handled through commands,
    not through the DAO layer. This ensures proper variant study management.
    """
    pass
