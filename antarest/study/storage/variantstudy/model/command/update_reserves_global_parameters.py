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
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserves_global_parameters_model import (
    ReservesGlobalParameters,
    ReservesGlobalParametersUpdate,
    update_reserves_global_parameters,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateReservesGlobalParameters(ICommand):
    """
    Command used to update the reserves global parameters for a given area.
    """

    command_name: CommandName = CommandName.UPDATE_RESERVES_GLOBAL_PARAMETERS

    area_id: str
    parameters: ReservesGlobalParametersUpdate

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[ReservesGlobalParameters]:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError("Reserves global parameters are not valid for study version before 10.0")

        current = study_data.get_reserves_global_parameters(self.area_id)
        new_params = update_reserves_global_parameters(current, self.parameters)
        study_data.save_reserves_global_parameters(self.area_id, new_params)
        return command_succeeded(
            message=f"Reserves global parameters updated for area {self.area_id}.", result=new_params
        )

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "parameters": self.parameters.model_dump(mode="json", exclude_none=True),
            },
            study_version=self.study_version,
        )
