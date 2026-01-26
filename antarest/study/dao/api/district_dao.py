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
from typing import Sequence

from antarest.study.business.model.district_model import (
    District,
)


class ReadOnlyDistrictDao(ABC):
    @abstractmethod
    def get_districts(self) -> Sequence[District]:
        """
        Get the list of districts defined in this study.

        Returns:
            The (unordered) list of Data Transfer Objects (DTO) representing districts.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_district(self, district_id: str) -> District:
        """
        Get the district  with the given ID.

        Returns:
            The object representing the district.
        """
        raise NotImplementedError()

    @abstractmethod
    def district_exists(self, district_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_invalid_areas_in_district(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study
        """
        raise NotImplementedError()


class DistrictDao(ReadOnlyDistrictDao):
    @abstractmethod
    def save_district(self, district: District) -> None:
        """
        Create a district or update the district if it already exists.

        Note:
            the `name` can't be updated because it is used as a unique identifier.

            Also, the areas in district will be stored under the "+" or "-" key depending if the apply filter is "remove_all" or "add_all".

            If the apply filter is "add_all" it means that this distrit will contain all existing areas except the ones in district.areas .

            Otherwise if the apply filter is "remove_all" it means the district contains only the areas in district.areas .

        Args:
            district: District object note that the areas field will contains exactly the area that will be stored.
            district_apply_filter: indicate whether this district include all areas except those given in district or only those .

        Raises:
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_district(
        self,
        district_id: str,
    ) -> None:
        """
        Remove a district from a study.

        Args:
            district_id: district identifier

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
        """
        raise NotImplementedError()
