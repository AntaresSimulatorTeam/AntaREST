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


from antarest.study.business.model.config.optimization_config import (
    OptimizationPreferences,
    OptimizationPreferencesUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_optimization_preferences import (
    UpdateOptimizationPreferences,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class OptimizationManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_optimization_preferences(self, study: StudyInterface) -> OptimizationPreferences:
        study_dao = study.get_study_dao()
        return study_dao.get_optimization_preferences()

    def update_optimization_preferences(self, study: StudyInterface, config: OptimizationPreferencesUpdate) -> None:
        """
        Set optimization config from the webapp form
        """

        command = UpdateOptimizationPreferences(parameters=config, command_context=self._command_context, study_version=study.version)
        study.add_commands([command])
