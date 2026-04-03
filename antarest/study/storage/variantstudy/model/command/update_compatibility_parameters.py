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

from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    CompatibilityParametersUpdate,
    update_compatibility_parameters,
    validate_compatibility_parameters_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateCompatibilityParameters(ICommand):
    """
    Command used to update compatibility parameters
    """

    command_name: CommandName = CommandName.UPDATE_COMPATIBILITY_PARAMETERS

    parameters: CompatibilityParametersUpdate

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[CompatibilityParameters]:
        validate_compatibility_parameters_against_version(self.study_version, self.parameters)

        if self.parameters.hydro_pmax is not None:
            study_data.convert_hydro_pmax(self.parameters.hydro_pmax)

        current_parameters = study_data.get_compatibility_parameters()
        new_parameters = update_compatibility_parameters(current_parameters, self.parameters)
        study_data.save_compatibility_parameters(new_parameters)
        return command_succeeded(message="Compatibility parameters updated successfully.", result=new_parameters)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"parameters": self.parameters.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )
