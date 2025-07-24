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
from typing import Dict

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


class HydroDao(ReadOnlyHydroDao):
    @abstractmethod
    def save_hydro_management(self, area_id: str, hydro_data: HydroManagement) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_inflow_structure(self, area_id: str, inflow_data: InflowStructure) -> None:
        raise NotImplementedError()
