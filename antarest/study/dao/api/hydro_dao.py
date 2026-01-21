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
from typing import Callable, Dict, Optional

import polars as pl

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.hydro_allocation_model import HydroAllocation
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationMatrix
from antarest.study.business.model.hydro_model import (
    HydroManagement,
    HydroProperties,
    InflowStructure,
)


class ReadOnlyHydroDao(ABC):
    @abstractmethod
    def get_all_hydro_properties(self) -> Dict[str, HydroProperties]:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        raise NotImplementedError()

    @abstractmethod
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError()


class HydroDao(ReadOnlyHydroDao):
    @abstractmethod
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_maxpower(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_reservoir(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_energy(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_run_of_river(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_modulation(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_credit_modulations(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_inflow_pattern(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_water_values(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_mingen(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_max_hourly_gen_power(self, area_id: str, matrix_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_max_hourly_pump_power(self, area_id: str, matrix_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_max_daily_gen_energy(self, area_id: str, matrix_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_hydro_max_daily_pump_energy(self, area_id: str, matrix_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def convert_hydro_pmax(
        self,
        hydro_pmax: str,
        matrix_service: ISimpleMatrixService,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        raise NotImplementedError()
