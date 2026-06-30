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

from antarest.core.exceptions import ReserveDefinitionsNotFound
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertificationMapping,
)
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId
from antarest.study.dao.file.common import (
    check_area_exists,
    get_thermal_reserve_participations_as_yaml_content,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal_reserve_certifications import (
    parse_thermal_reserves_certifications,
    serialize_thermal_reserve_certifications,
)
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
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        result = {}
        for area in self.get_file_study().config.areas:
            result[area] = self.get_all_thermal_reserve_certifications_for_area(area)
        return result

    @override
    def get_all_thermal_reserve_certifications_for_area(self, area_id: AreaId) -> ThermalReserveCertificationMapping:
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
            if invalid_reserves := set(reserves_dict) - set(existing_reserve_ids):
                raise ReserveDefinitionsNotFound({area_id: invalid_reserves})

            # Verify that the given thermals exist
            for thermal_ids in reserves_dict.values():
                for thermal_id in thermal_ids:
                    self.get_impl().thermal_exists(area_id, thermal_id)

            # Save the given certifications
            all_certifications = self.get_all_thermal_reserve_certifications_for_area(area_id)
            for thermal_id, value in reserves_dict.items():
                if thermal_id in all_certifications:
                    # First, save certifications for existing thermals
                    for reserve_id in value:
                        all_certifications[thermal_id][reserve_id] = data[area_id][thermal_id][reserve_id]
                else:
                    # Then, save certifications for new thermals
                    all_certifications[thermal_id] = value

            # Serialize the new content to write it into the YAML file
            yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
            for participation in yaml_content["participations"]:
                thermal_id = transform_name_to_id(participation["cluster"])
                certifications = all_certifications.pop(thermal_id)
                participation["certifications"] = serialize_thermal_reserve_certifications(certifications)

            for thermal_id, certifications in all_certifications.items():
                yaml_content["participations"].append(
                    {"cluster": thermal_id, "certifications": serialize_thermal_reserve_certifications(certifications)}
                )
