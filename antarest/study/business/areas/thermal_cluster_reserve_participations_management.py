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

from collections.abc import Sequence

from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
    ThermalClusterReserveParticipationCreation,
    ThermalClusterReserveParticipationUpdate,
    create_thermal_cluster_reserve_participation,
    update_thermal_cluster_reserve_participation,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.create_thermal_cluster_reserve_participation import (
    CreateThermalClusterReserveParticipation,
)
from antarest.study.storage.variantstudy.model.command.remove_thermal_cluster_reserve_participations import (
    RemoveThermalClusterReserveParticipations,
)
from antarest.study.storage.variantstudy.model.command.update_thermal_cluster_reserve_participations import (
    UpdateThermalClusterReserveParticipations,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThermalClusterReserveParticipationsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_participations(
        self, study: StudyInterface, area_id: str, thermal_id: str
    ) -> Sequence[ThermalClusterReserveParticipation]:
        return study.get_study_dao().get_all_thermal_cluster_reserve_participations_for_cluster(area_id, thermal_id)

    def get_participation(
        self, study: StudyInterface, area_id: str, thermal_id: str, reserve_id: str
    ) -> ThermalClusterReserveParticipation:
        return study.get_study_dao().get_thermal_cluster_reserve_participation(area_id, thermal_id, reserve_id)

    def create_participation(
        self,
        study: StudyInterface,
        area_id: str,
        thermal_id: str,
        data: ThermalClusterReserveParticipationCreation,
    ) -> ThermalClusterReserveParticipation:
        command = CreateThermalClusterReserveParticipation(
            area_id=area_id,
            thermal_id=thermal_id,
            parameters=data,
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return create_thermal_cluster_reserve_participation(data)

    def update_participation(
        self,
        study: StudyInterface,
        area_id: str,
        thermal_id: str,
        reserve_id: str,
        data: ThermalClusterReserveParticipationUpdate,
    ) -> ThermalClusterReserveParticipation:
        participation = self.get_participation(study, area_id, thermal_id, reserve_id)
        updated = update_thermal_cluster_reserve_participation(participation, data)

        command = UpdateThermalClusterReserveParticipations(
            participation_properties={area_id: {thermal_id: {reserve_id: data}}},
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return updated

    def delete_participations(
        self, study: StudyInterface, area_id: str, thermal_id: str, reserve_ids: Sequence[str]
    ) -> None:
        command = RemoveThermalClusterReserveParticipations(
            area_id=area_id,
            thermal_id=thermal_id,
            reserve_ids=reserve_ids,
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
