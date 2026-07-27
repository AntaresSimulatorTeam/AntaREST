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

from antarest.core.exceptions import ReserveDefinitionsNotFound, ThermalClusterNotFound
from antarest.study.business.model.reserve_certification_model import (
    StorageReserveCertificationMapping,
    ThermalReserveCertificationMapping,
)
from antarest.study.dao.api.reserve_certification_dao import ReserveCertificationDao
from antarest.study.dao.common import AreaId
from antarest.study.dao.file.common import (
    check_area_exists,
    get_thermal_reserve_participations_as_yaml_content,
    get_thermal_reserve_path,
)
from antarest.study.storage.rawstudy.model.filesystem.config.thermal_reserve_participations import (
    parse_thermal_reserves_certifications,
    parse_thermal_reserves_symmetries,
    serialize_thermal_reserve_participations,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyThermalReserveCertificationDao(ReserveCertificationDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        result = {}
        for area in self.get_file_study().config.areas:
            certifications = self.get_thermal_reserve_certifications(area)
            if certifications:
                # Only return areas with certifications to have the same behavior as the DB Dao.
                result[area] = certifications
        return result

    @override
    def get_thermal_reserve_certifications(self, area_id: AreaId) -> ThermalReserveCertificationMapping:
        data = get_thermal_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_thermal_reserves_certifications(data)

    @override
    def save_thermal_reserve_certifications(self, data: dict[AreaId, ThermalReserveCertificationMapping]) -> None:
        file_study = self.get_file_study()

        for area_id, reserves_dict in data.items():
            # Verify that the area exists
            check_area_exists(file_study.config, area_id)

            # Verify that the given reserves exist
            existing_reserve_ids = file_study.config.areas[area_id].reserves
            invalid_reserves: set[str] = set(reserves_dict) - set(existing_reserve_ids)  # type: ignore
            if invalid_reserves:
                raise ReserveDefinitionsNotFound({area_id: invalid_reserves})

            # Verify that the given thermals exist
            for thermal_ids in reserves_dict.values():
                for thermal_id in thermal_ids:
                    if not self.get_impl().thermal_exists(area_id, thermal_id):
                        raise ThermalClusterNotFound(area_id, thermal_id)

            yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
            symmetries = parse_thermal_reserves_symmetries(yaml_content)
            new_content = serialize_thermal_reserve_participations(symmetries, reserves_dict)

            # Saves the content into the YAML file
            file_study.tree.save(new_content, get_thermal_reserve_path(area_id))

    def save_storage_reserve_certifications(self, data: dict[AreaId, StorageReserveCertificationMapping]) -> None:
        # TODO: Implement this method
        pass

    def get_all_storage_reserve_certifications(self) -> dict[AreaId, StorageReserveCertificationMapping]:
        # TODO: Implement this method
        pass

    def get_storage_reserve_certifications(self, area_id: AreaId) -> StorageReserveCertificationMapping:
        # TODO: Implement this method
        pass
