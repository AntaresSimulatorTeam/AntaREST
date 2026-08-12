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

from antarest.core.exceptions import ReserveDefinitionNotFound, STStorageNotFound, ThermalClusterNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import check_symmetries_are_certified
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaAssetId,
    AreaId,
    STStorageReserveSymmetriesMapping,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
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


class FileStudyReserveSymmetriesDao(ReserveSymmetriesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            symmetries = self.get_thermal_reserve_symmetries(area)
            if symmetries:
                # Only return areas with symmetries to have the same behavior as the DB Dao.
                result[area] = symmetries
        return result

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_thermal_reserves_symmetries(yaml_content)

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        file_study = self.get_file_study()
        for area_id in data:
            check_area_exists(file_study.config, area_id)
            self._save_thermal_reserve_symmetries_for_area(area_id, data[area_id])

    def _save_thermal_reserve_symmetries_for_area(
        self, area_id: AreaId, data: dict[AreaAssetId, ReserveSymmetries]
    ) -> None:
        file_study = self.get_file_study()
        for thermal_id, symmetries in data.items():
            self._check_thermal_exists_in_area(area_id, thermal_id)
            self._check_reserve_definitions_exist_in_symmetries(area_id, symmetries)

        yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
        certifications = parse_thermal_reserves_certifications(yaml_content)

        # Verify that the thermals are certified on the reserves they are symmetric on
        check_symmetries_are_certified(area_id, data, certifications)

        new_content = serialize_thermal_reserve_participations(data, certifications)

        # Saves the content into the YAML file
        file_study.tree.save(new_content, get_thermal_reserve_path(area_id))

    def _check_thermal_exists_in_area(self, area_id: str, thermal_id: str) -> None:
        if not self.get_impl().thermal_exists(area_id, thermal_id):
            raise ThermalClusterNotFound(area_id, thermal_id)

    @override
    def get_all_st_storage_reserve_symmetries(self) -> STStorageReserveSymmetriesMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            symmetries = self.get_st_storage_reserve_symmetries(area)
            if symmetries:
                # Only return areas with symmetries to have the same behavior as the DB Dao.
                result[area] = symmetries
        return result

    @override
    def get_st_storage_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        yaml_content = get_st_storage_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_st_storage_reserves_symmetries(yaml_content)

    @override
    def save_st_storage_reserve_symmetries(self, data: STStorageReserveSymmetriesMapping) -> None:
        file_study = self.get_file_study()
        for area_id in data:
            check_area_exists(file_study.config, area_id)
            self._save_st_storage_reserve_symmetries_for_area(area_id, data[area_id])

    def _save_st_storage_reserve_symmetries_for_area(
        self, area_id: AreaId, new_symmetries: dict[AreaAssetId, ReserveSymmetries]
    ) -> None:
        file_study = self.get_file_study()
        for asset_id, symmetries in new_symmetries.items():
            self._check_st_storage_exists_in_area(area_id, asset_id)
            self._check_reserve_definitions_exist_in_symmetries(area_id, symmetries)

        yaml_content = get_st_storage_reserve_participations_as_yaml_content(area_id, file_study)
        certifications = parse_st_storage_reserves_certifications(yaml_content)
        new_content = serialize_st_storage_reserve_participations(new_symmetries, certifications)

        # Saves the content into the YAML file
        file_study.tree.save(new_content, get_st_storage_reserve_path(area_id))

    def _check_st_storage_exists_in_area(self, area_id: str, asset_id: str) -> None:
        if not self.get_impl().st_storage_exists(area_id, asset_id):
            raise STStorageNotFound(area_id, asset_id)

    def _check_reserve_definitions_exist_in_symmetries(
        self, storage_id: str, symmetries: list[list[ReserveDefinitionId]]
    ) -> None:
        for symmetry in symmetries:
            for reserve_id in symmetry:
                if not self.get_impl().reserve_definition_exists(storage_id, reserve_id):
                    raise ReserveDefinitionNotFound(storage_id, reserve_id)
