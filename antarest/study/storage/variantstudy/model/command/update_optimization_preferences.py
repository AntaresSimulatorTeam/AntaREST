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
from typing import Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    OptimizationPreferencesUpdate,
    update_optimization_preferences,
    validate_optimization_preferences_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateOptimizationPreferences(ICommand):
    """
    Command used to update the optimization preferences
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_OPTIMIZATION_PREFERENCES

    # Command parameters
    # ==================

    parameters: OptimizationPreferencesUpdate

    @model_validator(mode="after")
    def validate_against_version(self) -> Self:
        validate_optimization_preferences_against_version(self.study_version, self.parameters)
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[OptimizationPreferences]:
        current_config = study_data.get_optimization_preferences()
        new_config = update_optimization_preferences(current_config, self.parameters)
        study_data.save_optimization_preferences(new_config)
        return command_succeeded("Optimization config updated successfully.", result=new_config)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"parameters": self.parameters.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )
