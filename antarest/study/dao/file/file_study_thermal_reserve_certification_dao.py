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
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from typing_extensions import override

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyThermalReserveCertificationDao(ThermalReserveCertificationDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermal_reserve_certifications(self) -> ThermalReserveCertificationsMapping:
        raise NotImplementedError()

    @override
    def get_all_thermal_reserve_certifications_for_cluster(
            self, area_id: AreaId, thermal_id: ThermalId
    ) -> dict[ReserveDefinitionId, ThermalReserveCertification]:
        raise NotImplementedError()


    @override
    def get_thermal_reserve_certification(self, area_id: AreaId, thermal_id: ThermalId,
                                          reserve_id: str) -> ThermalReserveCertification:
        raise NotImplementedError()

    @override
    def thermal_reserve_certification_exists(self, area_id: AreaId, thermal_id: ThermalId, reserve_id: str) -> bool:
        raise NotImplementedError()


    @override
    def save_thermal_reserve_certifications(
            self,
            data: dict[AreaId, dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]],
    ) -> None:
        raise NotImplementedError()


    @override
    def delete_thermal_reserve_certifications(self, area_id: AreaId, thermal_id: ThermalId,
                                              reserve_ids: list[ReserveDefinitionId]) -> None:
        raise NotImplementedError()