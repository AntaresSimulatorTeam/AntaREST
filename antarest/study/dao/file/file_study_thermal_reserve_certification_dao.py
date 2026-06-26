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
from typing import TYPE_CHECKING, Any

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
    serialize_thermal_reserve_certification,
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
            check_area_exists(file_study.config, area_id)

            ini_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)

            for k, participation in enumerate(ini_content.get("participations", [])):
                thermal_id = transform_name_to_id(participation["cluster"])
                if thermal_id in thermal_dict:
                    # Empties `thermal_dict` to only keep in the end the certifications that are not already in the file
                    reserves_dict = thermal_dict.pop(thermal_id)
                    new_certifications = []
                    for certification in participation["certifications"]:
                        reserve_id = ReserveDefinitionId(transform_name_to_id(certification["reserve"]))
                        if reserve_id not in reserves_dict:
                            # Nothing to do
                            new_certifications.append(certification)
                        else:
                            # Add the new certification
                            data = serialize_thermal_reserve_certification(reserve_id, reserves_dict[reserve_id])
                            new_certifications.append(data)
                    # Replace the old certifications
                    # todo: We're missing the `symmetries` code.
                    ini_content["participations"][k] = new_certifications

            # Handle the remaining thermals which did not exist in the file.
            new_thermals = []
            for thermal_id, reserves_dict in thermal_dict.items():
                new_certifications = []
                for reserve_id, certification in reserves_dict.items():
                    new_certifications.append(serialize_thermal_reserve_certification(reserve_id, certification))
                new_thermals.append({"cluster": thermal_id, "certifications": new_certifications})

            ini_content.setdefault("participations", []).extend(new_thermals)

            # Save the new content
            file_study.tree.save(ini_content, get_thermal_reserve_path(area_id))

    @override
    def delete_thermal_reserve_certifications(
        self, area_id: AreaId, thermal_id: ThermalId, reserve_ids: list[ReserveDefinitionId]
    ) -> None:
        if not reserve_ids:
            return

        file_study = self.get_file_study()

        current_ini_content = get_thermal_reserve_participations_as_yaml_content(area_id, file_study)

        all_certifications = parse_thermal_reserves_certifications(current_ini_content)

        # Remove the given reserve ids from the existing certifications
        if thermal_id not in all_certifications:
            raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_id=reserve_ids[0])

        for reserve_id in reserve_ids:
            if reserve_id not in all_certifications[thermal_id]:
                raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_id=reserve_id)

            del all_certifications[thermal_id][reserve_id]

        # Fill the new file content
        ini_content = []
        for thermal_id, reserves_dict in all_certifications.items():
            thermal_content: dict[str, Any] = {"cluster": thermal_id, "certifications": []}
            for reserve_id, certification in reserves_dict.items():
                thermal_content["certifications"].append(
                    serialize_thermal_reserve_certification(reserve_id, certification)
                )
            ini_content.append(thermal_content)
        final_content = {"participations": ini_content}

        # Save the new content
        # todo: We're missing the `symmetries` code, so when removing one, we're removing all symmetries from the file.

        file_study.tree.save(final_content, get_thermal_reserve_path(area_id))

    def get_all_certifications_for_area(
        self, area_id: AreaId
    ) -> dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]:
        data = get_thermal_reserve_participations_as_yaml_content(area_id, self.get_file_study())
        return parse_thermal_reserves_certifications(data)
