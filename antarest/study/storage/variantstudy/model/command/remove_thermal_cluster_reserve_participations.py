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

from pydantic import model_validator
from typing_extensions import Self, override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveThermalClusterReserveParticipations(ICommand):
    """
    Command used to remove thermal cluster reserve participations from a cluster.
    """

    command_name: CommandName = CommandName.REMOVE_THERMAL_CLUSTER_RESERVE_PARTICIPATIONS

    area_id: str
    thermal_id: str
    reserve_ids: Sequence[ReserveDefinitionId]

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError(
                "Thermal cluster reserve participations are not valid for study version before 10.0"
            )
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        study_data.delete_thermal_cluster_reserve_participations(self.area_id, self.thermal_id, self.reserve_ids)
        return command_succeeded(
            f"Reserve participation(s) {list(self.reserve_ids)} for thermal cluster "
            f"'{self.thermal_id}' inside area '{self.area_id}' deleted",
            result=None,
        )

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "thermal_id": self.thermal_id,
                "reserve_ids": list(self.reserve_ids),
            },
            study_version=self.study_version,
        )
