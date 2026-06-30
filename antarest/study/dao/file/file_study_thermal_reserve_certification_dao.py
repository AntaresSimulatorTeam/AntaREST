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
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertification,
    ThermalReserveCertificationMapping,
)
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId
from antarest.study.dao.file.common import (
    check_area_exists,
    get_thermal_reserve_participations_as_yaml_content,
    get_thermal_reserve_path,
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
            certifications = self.get_all_thermal_reserve_certifications_for_area(area)
            if certifications:
                # Only return areas with certifications to have the same behavior as the DB Dao.
                result[area] = certifications
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
            invalid_reserves: set[str] = set(reserves_dict) - set(existing_reserve_ids)  # type: ignore
            if invalid_reserves:
                raise ReserveDefinitionsNotFound({area_id: invalid_reserves})

            # Verify that the given thermals exist
            for thermal_ids in reserves_dict.values():
                for thermal_id in thermal_ids:
                    if not self.get_impl().thermal_exists(area_id, thermal_id):
                        raise ThermalClusterNotFound(area_id, thermal_id)

            # Save the given certifications
            all_certifications = self.get_all_thermal_reserve_certifications_for_area(area_id)
            for reserve_id, value in reserves_dict.items():
                if reserve_id in all_certifications:
                    # First, save certifications for existing reserves
                    for thermal_id in value:
                        all_certifications[reserve_id][thermal_id] = data[area_id][reserve_id][thermal_id]
                else:
                    # Then, save certifications for new reserves
                    all_certifications[reserve_id] = value

            # Reorganize data as the YAML file is organized by thermals and not by reserves
            thermal_certifications: dict[str, dict[ReserveDefinitionId, ThermalReserveCertification]] = {}
            for reserve_id, value in all_certifications.items():
                for thermal_id, certification in value.items():
                    thermal_certifications.setdefault(thermal_id, {})[reserve_id] = certification

            # Serialize the new content to write it into the YAML file
            yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)
            for participation in yaml_content["participations"]:
                thermal_id = transform_name_to_id(participation["cluster"])
                if thermal_id not in thermal_certifications:
                    # Means the file contains symmetries but no certifications for this thermal
                    continue
                certifications = thermal_certifications.pop(thermal_id)
                participation["certifications"] = serialize_thermal_reserve_certifications(certifications)

            for thermal_id, certifications in thermal_certifications.items():
                yaml_content["participations"].append(
                    {"cluster": thermal_id, "certifications": serialize_thermal_reserve_certifications(certifications)}
                )

            # Saves the content into the YAML file
            file_study.tree.save(yaml_content, get_thermal_reserve_path(area_id))
