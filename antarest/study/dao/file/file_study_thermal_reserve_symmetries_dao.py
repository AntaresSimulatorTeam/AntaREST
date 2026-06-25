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
from typing import TYPE_CHECKING

from typing_extensions import override

from antarest.study.business.model.thermal_reserve_symmetries_model import ThermalReserveSymmetry
from antarest.study.dao.api.thermal_reserve_symmetries_dao import ThermalReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyThermalReserveSymmetriesDao(ThermalReserveSymmetriesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        raise NotImplementedError()

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, list[ThermalReserveSymmetry]]:
        raise NotImplementedError()

    @override
    def set_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        raise NotImplementedError()
