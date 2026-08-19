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

from antarest.study.business.model.reserve_certification_model import (
    StorageReserveCertificationMapping,
    ThermalReserveCertificationMapping,
)
from antarest.study.dao.common import AreaId


class ReadOnlyReserveCertificationDao(ABC):
    @abstractmethod
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        """
        Returns the thermal reserve certifications of the whole study.

        Design notes:
        - If an area has no certification, it won't be present in the returned data.
        - If a thermal cluster has no certification, it also won't be present in the returned data.

        """
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_reserve_certifications(self, area_id: AreaId) -> ThermalReserveCertificationMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_st_storage_reserve_certifications(self) -> dict[AreaId, StorageReserveCertificationMapping]:
        raise NotImplementedError()

    @abstractmethod
    def get_st_storage_reserve_certifications(self, area_id: AreaId) -> StorageReserveCertificationMapping:
        raise NotImplementedError()


class ReserveCertificationDao(ReadOnlyReserveCertificationDao):
    @abstractmethod
    def save_thermal_reserve_certifications(
        self, new_certifications: dict[AreaId, ThermalReserveCertificationMapping]
    ) -> None:
        """
        Replace the thermal reserve certifications with the given one.

        Design notes:
        - If an area is absent from the given data, its certifications are not modified.
        - If a thermal cluster is absent from in the given data, its certifications will be removed.

        """
        raise NotImplementedError()

    @abstractmethod
    def save_st_storage_reserve_certifications(
        self, new_certifications: dict[AreaId, StorageReserveCertificationMapping]
    ) -> None:
        raise NotImplementedError()
