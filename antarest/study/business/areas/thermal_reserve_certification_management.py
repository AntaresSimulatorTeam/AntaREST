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
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertification,
    ThermalReserveCertificationCreation,
    ThermalReserveCertificationUpdate,
    create_thermal_reserve_certification,
    update_thermal_reserve_certification,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThermalReserveCertificationsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_certifications(
        self, study: StudyInterface, area_id: str, thermal_id: str
    ) -> dict[ReserveDefinitionId, ThermalReserveCertification]:
        return study.get_study_dao().get_all_thermal_reserve_certifications_for_cluster(area_id, thermal_id)

    def get_certification(
        self, study: StudyInterface, area_id: str, thermal_id: str, reserve_id: str
    ) -> ThermalReserveCertification:
        return study.get_study_dao().get_thermal_reserve_certification(area_id, thermal_id, reserve_id)

    def create_certification(
        self,
        study: StudyInterface,
        area_id: str,
        thermal_id: str,
        data: ThermalReserveCertificationCreation,
    ) -> ThermalReserveCertification:
        command = CreateThermalReserveCertification(
            area_id=area_id,
            thermal_id=thermal_id,
            parameters=data,
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return create_thermal_reserve_certification(data)

    def update_certification(
        self,
        study: StudyInterface,
        area_id: str,
        thermal_id: str,
        reserve_id: str,
        data: ThermalReserveCertificationUpdate,
    ) -> ThermalReserveCertification:
        certification = self.get_certification(study, area_id, thermal_id, reserve_id)
        updated = update_thermal_reserve_certification(certification, data)

        command = UpdateThermalReserveCertifications(
            certification_properties={area_id: {thermal_id: {reserve_id: data}}},
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return updated

    def delete_certifications(
        self, study: StudyInterface, area_id: str, thermal_id: str, reserve_ids: list[str]
    ) -> None:
        command = RemoveThermalReserveCertifications(
            area_id=area_id,
            thermal_id=thermal_id,
            reserve_ids=reserve_ids,
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
