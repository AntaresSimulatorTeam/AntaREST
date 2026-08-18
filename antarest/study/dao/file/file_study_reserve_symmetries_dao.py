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

from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import check_thermal_symmetries_integrity
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.file.common import (
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


class FileStudyThermalReserveSymmetriesDao(ReserveSymmetriesDao, ABC):
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
        check_thermal_symmetries_integrity(self.get_impl(), data)

        for area_id in data:
            self._save_reserve_symmetries(area_id, data[area_id])

    def _save_reserve_symmetries(self, area_id: AreaId, data: dict[ThermalId, ReserveSymmetries]) -> None:
        file_study = self.get_file_study()

        yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
        certifications = parse_thermal_reserves_certifications(yaml_content)
        new_content = serialize_thermal_reserve_participations(data, certifications)

        # Saves the content into the YAML file
        file_study.tree.save(new_content, get_thermal_reserve_path(area_id))
