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
from typing import Any, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
    ThermalClusterReserveParticipationUpdates,
    update_thermal_cluster_reserve_participation,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateThermalClusterReserveParticipations(ICommand):
    """
    Command used to update several thermal cluster reserve participations at once.
    """

    command_name: CommandName = CommandName.UPDATE_THERMAL_CLUSTER_RESERVE_PARTICIPATIONS

    participation_properties: ThermalClusterReserveParticipationUpdates

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError(
                "Thermal cluster reserve participations are not valid for study version before 10.0"
            )
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[dict[str, dict[str, list[ThermalClusterReserveParticipation]]]]:
        memory_mapping: dict[str, dict[str, list[ThermalClusterReserveParticipation]]] = {}

        for area_id, by_cluster in self.participation_properties.items():
            for thermal_id, by_reserve in by_cluster.items():
                existing = study_data.get_all_thermal_cluster_reserve_participations_for_cluster(area_id, thermal_id)
                existing_by_id = {p.id: p for p in existing}
                new_participations: list[ThermalClusterReserveParticipation] = []
                for reserve_id, new_properties in by_reserve.items():
                    if reserve_id not in existing_by_id:
                        return command_failed(
                            f"Reserve participation '{reserve_id}' for thermal cluster "
                            f"'{thermal_id}' in area '{area_id}' is not found."
                        )
                    new_participations.append(
                        update_thermal_cluster_reserve_participation(existing_by_id[reserve_id], new_properties)
                    )
                memory_mapping.setdefault(area_id, {})[thermal_id] = new_participations

        study_data.save_thermal_cluster_reserve_participations(memory_mapping)

        return command_succeeded("All thermal cluster reserve participations updated", result=memory_mapping)

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, Any] = {}
        for area_id, by_cluster in self.participation_properties.items():
            for thermal_id, by_reserve in by_cluster.items():
                for reserve_id, properties in by_reserve.items():
                    args.setdefault(area_id, {}).setdefault(thermal_id, {})[reserve_id] = properties.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    )

        return CommandDTO(
            action=self.command_name.value,
            args={"participation_properties": args},
            study_version=self.study_version,
        )
