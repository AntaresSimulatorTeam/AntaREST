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

from typing import Any, Dict, Final, List, Optional

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
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
    # version 2: remove unused `metadata` field
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    area_name: str

    @model_validator(mode="before")
    @classmethod
    def _validate_metadata(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        # Handle version 1 format: {"area_name": "x", "metadata": {...}}
        # The metadata field was never used and is dropped in version 2
        if "metadata" in values:
            values.pop("metadata")
        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        study_data.save_area(self.area_name, self.command_context)
        return command_succeeded(message=f"Area '{self.area_name}' created")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={"area_name": self.area_name},
            study_version=self.study_version,
            version=self._SERIALIZATION_VERSION,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
