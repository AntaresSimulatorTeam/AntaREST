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

from typing import Optional

from typing_extensions import override

from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParametersUpdate
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class HydroPmaxConverter(ICommand):
    """
    Command used to convert hydro-pmax value from daily to hourly and vice versa
    """

    command_name: CommandName = CommandName.CONVERT_HYDRO_PMAX

    parameters: CompatibilityParametersUpdate

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if self.parameters.hydro_pmax is None:
            return CommandOutput(
                status=False,
                message="hydro_pmax parameter is required but was not provided.",
            )
        study_data.convert_hydro_pmax(self.parameters.hydro_pmax, self.command_context.matrix_service)
        return command_succeeded(message="Hydro pmax converted successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"parameters": self.parameters.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )
