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

"""
Database implementation of DistrictDao.

This module provides database-backed storage for districts when storage_mode=DATABASE.
"""

from typing import Sequence

from typing_extensions import override

from antarest.study.business.model.district_model import District
from antarest.study.dao.api.district_dao import DistrictDao


class DatabaseDistrictDao(DistrictDao):
    @override
    def save_district(self, district: District) -> None:
        pass

    @override
    def remove_district(self, district_id: str) -> None:
        pass

    @override
    def get_districts(self) -> Sequence[District]:
        pass

    @override
    def get_district(self, district_id: str) -> District:
        pass

    @override
    def district_exists(self, district_id: str) -> bool:
        pass

    @override
    def get_invalid_areas_in_district(self, areas: list[str]) -> list[str]:
        pass
