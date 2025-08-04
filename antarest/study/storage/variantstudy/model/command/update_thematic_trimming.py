# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from typing import List, Optional

from typing_extensions import override

from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimmingUpdate,
    update_thematic_trimming,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateThematicTrimming(ICommand):
    """
    Command used to update the thematic trimming
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_THEMATIC_TRIMMING

    # Command parameters
    # ==================

    parameters: ThematicTrimmingUpdate

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_thematic_trimming = study_data.get_thematic_trimming()
        final_thematic_trimming = update_thematic_trimming(current_thematic_trimming, self.parameters)
        study_data.save_thematic_trimming(final_thematic_trimming)
        return command_succeeded("Thematic trimming updated successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"parameters": self.parameters.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
