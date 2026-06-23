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

from antarest.core.exceptions import ThermalReserveCertificationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping
from antarest.study.storage.rawstudy.model.filesystem.config.thermal_reserve_certifications import \
    parse_thermal_reserves_certifications
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

def _thermal_reserve_path(area_id: str) -> list[str]:
    return ["input", "thermal", "clusters", area_id, "reserves-participations"]

class FileStudyThermalReserveCertificationDao(ThermalReserveCertificationDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermal_reserve_certifications(self) -> ThermalReserveCertificationsMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            result[area] = self._get_all_certifications_for_area(area)
        return result

    @override
    def get_all_thermal_reserve_certifications_for_cluster(
            self, area_id: AreaId, thermal_id: ThermalId
    ) -> dict[ReserveDefinitionId, ThermalReserveCertification]:
        return self._get_all_certifications_for_area(area_id).get(thermal_id, {})

    @override
    def get_thermal_reserve_certification(self, area_id: AreaId, thermal_id: ThermalId,
                                          reserve_id: ReserveDefinitionId) -> ThermalReserveCertification:
        certifications = self._get_all_certifications_for_area(area_id).get(thermal_id, {})
        if reserve_id in certifications:
            return certifications[reserve_id]

        raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_id)

    @override
    def thermal_reserve_certification_exists(self, area_id: AreaId, thermal_id: ThermalId, reserve_id: ReserveDefinitionId) -> bool:
        return reserve_id in self._get_all_certifications_for_area(area_id).get(thermal_id, {})

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

    def _get_all_certifications_for_area(self, area_id: AreaId) -> dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]:
        data = self.get_file_study().tree.get(_thermal_reserve_path(area_id))
        return parse_thermal_reserves_certifications(data)