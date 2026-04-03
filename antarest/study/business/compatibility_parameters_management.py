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
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    CompatibilityParametersUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_compatibility_parameters import (
    UpdateCompatibilityParameters,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class CompatibilityParamsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_compatibility_parameters(self, study: StudyInterface) -> CompatibilityParameters:
        """
        Get Compatibility parameters values for the webapp form
        """
        return study.get_study_dao().get_compatibility_parameters()

    def update_compatibility_parameters(
        self, study: StudyInterface, parameters: CompatibilityParametersUpdate
    ) -> CompatibilityParameters:
        """
        Update Compatibility parameters values from the webapp form
        """

        commands = [
            UpdateCompatibilityParameters(
                parameters=parameters,
                command_context=self._command_context,
                study_version=study.version,
            )
        ]

        study.add_commands(commands)
        return self.get_compatibility_parameters(study)
