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
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    CompatibilityParametersUpdate,
    update_compatibility_parameters,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateReservesEnabled(ICommand):
    """
    Command used to update the reserves_enabled compatibility parameter.
    """

    command_name: CommandName = CommandName.UPDATE_RESERVES_ENABLED

    reserves_enabled: bool

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[CompatibilityParameters]:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError(
                "Field reserves_enabled is not a valid field for study version before 10.0"
            )

        current_parameters = study_data.get_compatibility_parameters()
        new_parameters = update_compatibility_parameters(
            current_parameters, CompatibilityParametersUpdate(reserves_enabled=self.reserves_enabled)
        )
        study_data.save_compatibility_parameters(new_parameters)
        return command_succeeded(message="Reserves enabled updated successfully.", result=new_parameters)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"reserves_enabled": self.reserves_enabled},
            study_version=self.study_version,
        )
