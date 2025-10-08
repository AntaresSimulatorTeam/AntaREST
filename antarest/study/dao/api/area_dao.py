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

from antarest.study.business.model.area_model import Area, AreaUIUpdate


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

    Note: Write operations (create, update, delete) are handled through the DAO,
    which abstracts the storage implementation (filesystem, database, etc.).
    """

    @abstractmethod
    def save_area(self, area_name: str, command_context: Any) -> None:
        """
        Create a new area in the study.

        Args:
            area_name: The name of the area to create.
            command_context: Command context containing generator constants for matrices.

        Raises:
            ValueError: If the area already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_area(self, area_id: str) -> None:
        """
        Delete an area from the study.

        Args:
            area_id: The area identifier to delete.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_area_ui(self, area_id: str, layer: str, area_ui_update: AreaUIUpdate) -> None:
        """
        Update an area's UI properties (position and color) for a specific layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc.).
            area_ui_update: The UI properties to update (x, y, color_rgb).

        Raises:
            AreaNotFound: If the area does not exist.
        """
        raise NotImplementedError()

    @abstractmethod
    def save_layer_areas(self, layer_id: str, area_ids: List[str]) -> None:
        """
        Update the areas associated with a specific layer.

        Args:
            layer_id: The layer identifier.
            area_ids: List of area identifiers to associate with the layer.
                     Areas not in this list will be removed from the layer.

        Raises:
            LayerNotFound: If the layer does not exist.
        """
        raise NotImplementedError()
