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

from typing import Dict, List, Optional

from pydantic import Field
from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


# Constants kept here for backward compatibility with NodalOptimization import
# These are now used in the DAO layer
class NodalOptimization:
    NON_DISPATCHABLE_POWER: bool = True
    DISPATCHABLE_HYDRO_POWER: bool = True
    OTHER_DISPATCHABLE_POWER: bool = True
    SPREAD_UNSUPPLIED_ENERGY_COST: float = 0.000000
    SPREAD_SPILLED_ENERGY_COST: float = 0.000000
    UNSERVERDDENERGYCOST: float = 0.000000
    SPILLEDENERGYCOST: float = 0.000000


class CreateArea(ICommand):
    """
    Command used to create a new area in the study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_AREA

    # Command parameters
    # ==================

    area_name: str

    # The `metadata` attribute is added to ensure upward compatibility with previous versions.
    # Ideally, this attribute should be of type `PatchArea`, but as it is not used,
    # we choose to declare it as an empty dictionary.
    # fixme: remove this attribute in the next version if it is not used by the "Script R" team,
    #  or if we don't want to support this feature.
    metadata: Dict[str, str] = Field(default_factory=dict, description="Area metadata: country and tag list")

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        try:
            study_data.save_area(self.area_name, self.command_context)
            return command_succeeded(message=f"Area '{self.area_name}' created")
        except ValueError as e:
            return command_failed(message=str(e))

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value, args={"area_name": self.area_name}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
