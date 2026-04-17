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

from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.common import ReservesGlobalParametersMapping


class ReadOnlyReservesGlobalParametersDao(ABC):
    @abstractmethod
    def get_reserves_global_parameters(self, area_id: str) -> ReservesGlobalParameters:
        raise NotImplementedError()

    @abstractmethod
    def get_all_reserves_global_parameters(self) -> ReservesGlobalParametersMapping:
        raise NotImplementedError()


class ReservesGlobalParametersDao(ReadOnlyReservesGlobalParametersDao):
    @abstractmethod
    def save_reserves_global_parameters(self, mapping: ReservesGlobalParametersMapping) -> None:
        raise NotImplementedError()
