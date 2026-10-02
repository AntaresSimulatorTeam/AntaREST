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
from typing import TYPE_CHECKING, Callable

from typing_extensions import override

from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import (
    check_hydro_symmetries_integrity,
    check_st_storage_symmetries_integrity,
    check_thermal_symmetries_integrity,
)
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    HydroReserveSymmetriesMapping,
    ReserveSymmetriesMapping,
    StStorageId,
    STStorageReserveSymmetriesMapping,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.file.common import (
    get_hydro_reserve_participations_as_yaml_content,
    get_hydro_reserve_path,
    get_st_storage_reserve_participations_as_yaml_content,
    get_st_storage_reserve_path,
    get_thermal_reserve_participations_as_yaml_content,
    get_thermal_reserve_path,
)
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_hydro_reserves_certifications,
    parse_hydro_reserves_symmetries,
    parse_st_storage_reserves_certifications,
    parse_st_storage_reserves_symmetries,
    parse_thermal_reserves_certifications,
    parse_thermal_reserves_symmetries,
    serialize_hydro_reserve_participations,
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
        return self._get_all_reserve_symmetries(self.get_thermal_reserve_symmetries)

    @override
    def get_all_st_storage_reserve_symmetries(self) -> STStorageReserveSymmetriesMapping:
        return self._get_all_reserve_symmetries(self.get_st_storage_reserve_symmetries)

    def _get_all_reserve_symmetries(
        self, func: Callable[[AreaId], dict[str, ReserveSymmetries]]
    ) -> ReserveSymmetriesMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            symmetries = func(area)
            if symmetries:
                # Only return areas with symmetries to have the same behavior as the DB Dao.
                result[area] = symmetries
        return result

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_thermal_reserves_symmetries(yaml_content)

    @override
    def get_st_storage_reserve_symmetries(self, area_id: AreaId) -> dict[StStorageId, ReserveSymmetries]:
        yaml_content = get_st_storage_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_st_storage_reserves_symmetries(yaml_content)

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        check_thermal_symmetries_integrity(self.get_impl(), data)

        file_study = self.get_file_study()
        memory_mapping = {}
        for area_id in data:
            yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
            certifications = parse_thermal_reserves_certifications(yaml_content)
            new_content = serialize_thermal_reserve_participations(data[area_id], certifications)
            memory_mapping[area_id] = new_content

        # Once we've validated all the contents, we can save them
        for area_id, new_content in memory_mapping.items():
            file_study.tree.save(new_content, get_thermal_reserve_path(area_id))

    @override
    def save_st_storage_reserve_symmetries(self, data: STStorageReserveSymmetriesMapping) -> None:
        check_st_storage_symmetries_integrity(self.get_impl(), data)

        file_study = self.get_file_study()
        memory_mapping = {}
        for area_id in data:
            yaml_content = get_st_storage_reserve_participations_as_yaml_content(area_id, file_study)
            certifications = parse_st_storage_reserves_certifications(yaml_content)
            new_content = serialize_st_storage_reserve_participations(data[area_id], certifications)
            memory_mapping[area_id] = new_content

        # Once we've validated all the contents, we can save them
        for area_id, new_content in memory_mapping.items():
            file_study.tree.save(new_content, get_st_storage_reserve_path(area_id))

    @override
    def get_all_hydro_reserve_symmetries(self) -> HydroReserveSymmetriesMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            symmetries = self.get_hydro_reserve_symmetries(area)
            if symmetries:
                # Only return areas with symmetries to have the same behavior as the DB Dao.
                result[area] = symmetries
        return result

    @override
    def get_hydro_reserve_symmetries(self, area_id: AreaId) -> ReserveSymmetries:
        yaml_content = get_hydro_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_hydro_reserves_symmetries(yaml_content)

    @override
    def save_hydro_reserve_symmetries(self, data: HydroReserveSymmetriesMapping) -> None:
        check_hydro_symmetries_integrity(self.get_impl(), data)

        file_study = self.get_file_study()
        memory_mapping = {}
        for area_id in data:
            yaml_content = get_hydro_reserve_participations_as_yaml_content(area_id, file_study)
            certifications = parse_hydro_reserves_certifications(yaml_content)
            new_content = serialize_hydro_reserve_participations(data[area_id], certifications)
            memory_mapping[area_id] = new_content

        # Once we've validated all the contents, we can save them
        for area_id, new_content in memory_mapping.items():
            file_study.tree.save(new_content, get_hydro_reserve_path(area_id))
