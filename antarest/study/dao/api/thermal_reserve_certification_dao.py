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

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping


class ReadOnlyThermalReserveCertificationDao(ABC):
    @abstractmethod
    def get_all_thermal_reserve_certifications(self) -> ThermalReserveCertificationsMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermal_reserve_certifications_for_area(
        self, area_id: AreaId
    ) -> dict[ReserveDefinitionId, dict[ThermalId, ThermalReserveCertification]]:
        raise NotImplementedError()


class ThermalReserveCertificationDao(ReadOnlyThermalReserveCertificationDao):
    @abstractmethod
    def save_thermal_reserve_certifications(self, data: ThermalReserveCertificationsMapping) -> None:
        raise NotImplementedError()
