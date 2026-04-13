# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import polars as pl

from antarest.study.business.model.area_model import AreaInfo, AreaUI, AreaUIData
from antarest.study.dao.common import AreaSeriesMapping, AreaUiMapping


class ReadOnlyAreaDao(ABC):
    @abstractmethod
    def get_all_area_ids(self) -> list[str]:
        """
        Retrieve all physical areas of a study.

        Returns:
            The list of areas with their basic information.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all_areas_info(self) -> list[AreaInfo]:
        """
        Retrieve all physical areas of a study.

        Returns:
            The list of areas with their basic information.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all_areas_ui_info(self) -> dict[str, AreaUIData]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            A dictionary mapping area IDs to their UI data.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_area_ui(self, area_id: str, layer: str = "0") -> AreaUI:
        """
        Retrieve UI information for a specific area and layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc.). Defaults to "0".

        Returns:
            The UI properties for the area (x, y, color_rgb).

        Raises:
            AreaNotFound: If the area does not exist.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_invalid_area_ids(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study
        """
        raise NotImplementedError()

    @abstractmethod
    def get_load(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_misc_gen(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_reserves(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_solar(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_wind(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_all_load(self) -> AreaSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_misc_gen(self) -> AreaSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_reserves(self) -> AreaSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_solar(self) -> AreaSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_wind(self) -> AreaSeriesMapping:
        raise NotImplementedError()


class AreaDao(ReadOnlyAreaDao):
    """
    DAO for area operations.

    Note: Write operations (create, update, delete) are handled through the DAO,
    which abstracts the storage implementation (filesystem, database, etc.).
    """

    @abstractmethod
    def save_area(self, area_name: str) -> None:
        """
        Create a new area in the study.

        Args:
            area_name: The name of the area to create.

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
    def save_area_ui(self, data: AreaUiMapping) -> None:
        """Save several area UI properties (position and color) for given layers."""
        raise NotImplementedError()

    @abstractmethod
    def save_layer_areas(self, layer_id: str, area_ids: list[str]) -> None:
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

    @abstractmethod
    def save_load(self, series: AreaSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_misc_gen(self, series: AreaSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_reserves(self, series: AreaSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_solar(self, series: AreaSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_wind(self, series: AreaSeriesMapping) -> None:
        raise NotImplementedError()
