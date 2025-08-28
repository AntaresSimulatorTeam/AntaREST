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
from typing import Optional, Sequence

from antarest.study.business.model.district_model import (
    District,
    DistrictBaseFilter,
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
        Get the list of districts defined in this study.

        Returns:
            The (unordered) list of Data Transfer Objects (DTO) representing districts.
        """
        raise NotImplementedError()

    @abstractmethod
    def district_exists(self, district_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_invalid_areas(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study
        """
        # TODO this method should be moved to the area DAO when we'll implement it
        raise NotImplementedError()


class DistrictDao(ReadOnlyDistrictDao):
    @abstractmethod
    def save_district(self, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> None:
        """
        Update the properties of a district and/or the areas list.

        Note:
            the `name` can't be updated because it is used as a unique identifier.

        Args:
            district_id: district identifier
            dto: Data Transfer Objects (DTO) used for update.

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
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
