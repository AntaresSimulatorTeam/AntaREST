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
from collections.abc import Sequence

import polars as pl

from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.common import AreaId, ThermalId, ThermalSeriesMapping


class ReadOnlyThermalDao(ABC):
    @abstractmethod
    def get_all_thermals(self) -> dict[AreaId, dict[ThermalId, ThermalCluster]]:
        """
        Returns a mapping of area ID to cluster IDs to cluster.

        Note that areas with no clusters will be absent from the returned mapping.
        """
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

    @abstractmethod
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_co2_cost(self) -> ThermalSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_fuel_cost(self) -> ThermalSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_series(self) -> ThermalSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_modulation(self) -> ThermalSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_thermals_prepro(self) -> ThermalSeriesMapping:
        raise NotImplementedError()


class ThermalDao(ReadOnlyThermalDao):
    @abstractmethod
    def save_thermals(self, data: dict[AreaId, list[ThermalCluster]]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_prepro(self, series: ThermalSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_modulation(self, series: ThermalSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_series(self, series: ThermalSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_fuel_cost(self, series: ThermalSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_thermal_co2_cost(self, series: ThermalSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_thermal(self, area_id: AreaId, thermal_id: ThermalId) -> None:
        raise NotImplementedError()
