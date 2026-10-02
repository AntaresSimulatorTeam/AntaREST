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

from antarest.study.business.model.hydro_allocation_model import HydroAllocation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceHydroAllocation(ICommand):
    """
    Command used to replace hydro allocation for a particular area
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_HYDRO_ALLOCATION

    # Command parameters
    # ==================

    area_id: AreaId
    allocation: HydroAllocation

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        study_data.save_hydro_allocation({self.area_id: self.allocation})
        return command_succeeded(message=f"Hydro allocation for area {self.area_id} replaced successfully", result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "allocation": self.allocation.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )
