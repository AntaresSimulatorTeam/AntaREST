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
from dataclasses import dataclass
from typing import Optional

from typing_extensions import override

from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandApplicationResult,
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


@dataclass(frozen=True)
class ConvertHydroPMaxResult(CommandApplicationResult):
    data: HydroPmax


class ConvertHydroPmax(ICommand):
    """
    Command used to convert hydro-pmax value from daily to hourly and vice versa
    """

    command_name: CommandName = CommandName.CONVERT_HYDRO_PMAX

    hydro_pmax: HydroPmax

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.convert_hydro_pmax(self.hydro_pmax)
        result = ConvertHydroPMaxResult(data=self.hydro_pmax)
        return command_succeeded(message="Hydro pmax converted successfully.", result=result)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"hydro_pmax": self.hydro_pmax.value},
            study_version=self.study_version,
        )
