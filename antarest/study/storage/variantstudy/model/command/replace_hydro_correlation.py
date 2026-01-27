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

from antarest.study.business.model.hydro_correlation_model import HydroCorrelation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceHydroCorrelation(ICommand):
    """
    Command used to replace hydro correlation for the whole study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_HYDRO_CORRELATION

    # Command parameters
    # ==================

    area_id: str
    correlation: HydroCorrelation

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.save_hydro_correlation(self.area_id, self.correlation)
        return command_succeeded(message=f"Hydro correlation for area {self.area_id} replaced successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "correlation": self.correlation.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )
