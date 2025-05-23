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
from typing import Sequence

from antarest.study.business.model.thermal_cluster_model import ThermalCluster


class ReadOnlyThermalDao(ABC):
    @abstractmethod
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        raise NotImplementedError()

    @abstractmethod
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        raise NotImplementedError()


class ThermalDao(ReadOnlyThermalDao):
    @abstractmethod
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermals(self, area_id: str, thermals: Sequence[ThermalCluster]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_fuel_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        raise NotImplementedError()
