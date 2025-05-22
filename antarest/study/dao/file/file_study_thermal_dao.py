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

from typing_extensions import override

from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyThermalDao(ThermalDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_thermals(self) -> Sequence[ThermalCluster]:
        raise NotImplementedError()

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        raise NotImplementedError()

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        raise NotImplementedError()

    @override
    def save_thermal(self, thermal: ThermalCluster) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def delete_thermal(self, thermal: ThermalCluster) -> None:
        raise NotImplementedError()
