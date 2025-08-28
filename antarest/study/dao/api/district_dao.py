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
from typing import List

from antarest.study.business.model.district_model import District


class ReadOnlyDistrictDao(ABC):
    @abstractmethod
    def get_districts(self) -> List[District]:
        """Get all districts in the study."""
        raise NotImplementedError()

    @abstractmethod
    def get_district(self, district_id: str) -> District:
        """Get a specific district by ID."""
        raise NotImplementedError()

    @abstractmethod
    def district_exists(self, district_id: str) -> bool:
        """Check if a district exists."""
        raise NotImplementedError()


class DistrictDao(ReadOnlyDistrictDao):
    @abstractmethod
    def save_district(self, district: District) -> None:
        """Save a district."""
        raise NotImplementedError()

    @abstractmethod
    def delete_district(self, district_id: str) -> None:
        """Delete a district by ID."""
        raise NotImplementedError()