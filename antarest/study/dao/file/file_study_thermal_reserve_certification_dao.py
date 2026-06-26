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

from antarest.core.exceptions import ThermalReserveCertificationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping
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
    def get_all_thermal_reserve_certifications(self) -> ThermalReserveCertificationsMapping:
        result = {}
        for area in self.get_file_study().config.areas:
            result[area] = self.get_all_certifications_for_area(area)
        return result

    @override
    def get_all_thermal_reserve_certifications_for_cluster(
        self, area_id: AreaId, thermal_id: ThermalId
    ) -> dict[ReserveDefinitionId, ThermalReserveCertification]:
        return self.get_all_certifications_for_area(area_id).get(thermal_id, {})

    @override
    def get_thermal_reserve_certification(
        self, area_id: AreaId, thermal_id: ThermalId, reserve_id: ReserveDefinitionId
    ) -> ThermalReserveCertification:
        certifications = self.get_all_certifications_for_area(area_id).get(thermal_id, {})
        if reserve_id in certifications:
            return certifications[reserve_id]

        raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_id)

    @override
    def thermal_reserve_certification_exists(
        self, area_id: AreaId, thermal_id: ThermalId, reserve_id: ReserveDefinitionId
    ) -> bool:
        return reserve_id in self.get_all_certifications_for_area(area_id).get(thermal_id, {})

    @override
    def save_thermal_reserve_certifications(self, data: ThermalReserveCertificationsMapping) -> None:
        file_study = self.get_file_study()

        for area_id, thermal_dict in data.items():
            # Verify area and thermals exist
            check_area_exists(file_study.config, area_id)
            for thermal_id in thermal_dict:
                self.get_impl().thermal_exists(area_id, thermal_id)

            all_certifications = self.get_all_certifications_for_area(area_id)
            for thermal_id, value in thermal_dict.items():
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

            for thermal_id, certifications in all_certifications:
                print("todo")

    @override
    def delete_thermal_reserve_certifications(
        self, area_id: AreaId, thermal_id: ThermalId, reserve_ids: list[ReserveDefinitionId]
    ) -> None:
        if not reserve_ids:
            return

        file_study = self.get_file_study()

        yaml_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)

        thermal_exists = False
        for k, participation in enumerate(yaml_content["participations"]):
            cluster_id = transform_name_to_id(participation["cluster"])
            if cluster_id == thermal_id:
                certifications = participation["certifications"]
                new_certifications = []
                for certification in certifications:
                    reserve_id = ReserveDefinitionId(transform_name_to_id(certification["reserve"]))
                    if reserve_id not in reserve_ids:
                        new_certifications.append(certification)
                participation["certifications"] = new_certifications
                if len(new_certifications) != len(certifications) - len(reserve_ids):
                    raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_ids=set(reserve_ids))
                thermal_exists = True
                break

        if not thermal_exists:
            # Means the thermal exists in the area but not in the reserve participations YAML file
            raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_ids=set(reserve_ids))

        # Save the new content in the YAML file
        file_study.tree.save(yaml_content, get_thermal_reserve_path(area_id))

    def get_all_certifications_for_area(
        self, area_id: AreaId
    ) -> dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]:
        data = get_thermal_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_thermal_reserves_certifications(data)
