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

from antarest.core.exceptions import ReserveDefinitionsNotFound, STStorageNotFound, ThermalClusterNotFound
from antarest.study.business.model.reserve_certification_model import (
    ReserveCertification,
    StorageReserveCertificationMapping,
    ThermalReserveCertification,
    ThermalReserveCertificationMapping,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.dao.api.reserve_certification_dao import ReserveCertificationDao
from antarest.study.dao.common import AreaId
from antarest.study.dao.file.common import (
    check_area_exists,
    get_st_storage_reserve_participations_as_yaml_content,
    get_st_storage_reserve_path,
    get_thermal_reserve_participations_as_yaml_content,
    get_thermal_reserve_path,
)
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_st_storage_reserves_certifications,
    parse_st_storage_reserves_symmetries,
    parse_thermal_reserves_certifications,
    parse_thermal_reserves_symmetries,
    serialize_st_storage_reserve_participations,
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
    def save_thermal_reserve_certifications(
        self, new_certifications: dict[AreaId, ThermalReserveCertificationMapping]
    ) -> None:
        file_study = self.get_file_study()

        for area_id, reserves_dict in new_certifications.items():
            check_area_exists(file_study.config, area_id)
            self._check_reserves_exist(area_id, file_study, reserves_dict)
            self._check_all_thermals_exist_in_area(area_id, reserves_dict)

            yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
            symmetries = parse_thermal_reserves_symmetries(yaml_content)
            new_content = serialize_thermal_reserve_participations(symmetries, reserves_dict)

            # Saves the content into the YAML file
            file_study.tree.save(new_content, get_thermal_reserve_path(area_id))

    @staticmethod
    def _check_reserves_exist(
        area_id: str, file_study: FileStudy, reserves_dict: dict[ReserveDefinitionId, dict[str, ReserveCertification]]
    ):
        existing_reserve_ids = file_study.config.areas[area_id].reserves
        invalid_reserves: set[str] = set(reserves_dict) - set(existing_reserve_ids)  # type: ignore
        if invalid_reserves:
            raise ReserveDefinitionsNotFound({area_id: invalid_reserves})

    def _check_all_thermals_exist_in_area(
        self, area_id: str, reserves_dict: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]
    ):
        for thermal_ids in reserves_dict.values():
            for thermal_id in thermal_ids:
                if not self.get_impl().thermal_exists(area_id, thermal_id):
                    raise ThermalClusterNotFound(area_id, thermal_id)

    @override
    def save_st_storage_reserve_certifications(
        self, new_certifications: dict[AreaId, StorageReserveCertificationMapping]
    ) -> None:
        file_study = self.get_file_study()

        for area_id, reserves_dict in new_certifications.items():
            check_area_exists(file_study.config, area_id)
            self._check_reserves_exist(area_id, file_study, reserves_dict)
            self._check_all_st_storages_exist_in_area(area_id, reserves_dict)

            yaml_content = get_st_storage_reserve_participations_as_yaml_content(area_id, file_study)
            symmetries = parse_st_storage_reserves_symmetries(yaml_content)
            new_content = serialize_st_storage_reserve_participations(symmetries, reserves_dict)

            # Saves the content into the YAML file
            file_study.tree.save(new_content, get_st_storage_reserve_path(area_id))

    def _check_all_st_storages_exist_in_area(
        self, area_id: str, reserves_dict: dict[ReserveDefinitionId, dict[str, ReserveCertification]]
    ):
        for storage_ids in reserves_dict.values():
            for storage_id in storage_ids:
                if not self.get_impl().st_storage_exists(area_id, storage_id):
                    raise STStorageNotFound(area_id, storage_id)

    @override
    def get_all_st_storage_reserve_certifications(self) -> dict[AreaId, StorageReserveCertificationMapping]:
        result = {}
        for area in self.get_file_study().config.areas:
            certifications = self.get_st_storage_reserve_certifications(area)
            if certifications:
                # Only return areas with certifications to have the same behavior as the DB Dao.
                result[area] = certifications
        return result

    @override
    def get_st_storage_reserve_certifications(self, area_id: AreaId) -> StorageReserveCertificationMapping:
        data = get_st_storage_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_st_storage_reserves_certifications(data)
