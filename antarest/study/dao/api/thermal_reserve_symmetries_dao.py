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

from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetry
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)


class ReadOnlyThermalReserveSymmetriesDao(ABC):
    @abstractmethod
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, list[ReserveSymmetry]]:
        raise NotImplementedError()


class ThermalReserveSymmetriesDao(ReadOnlyThermalReserveSymmetriesDao):
    @abstractmethod
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        raise NotImplementedError()
