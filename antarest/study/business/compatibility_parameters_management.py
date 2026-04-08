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
    validate_compatibility_parameters_against_version,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.convert_hydro_pmax import ConvertHydroPmax
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_reserves_enabled import UpdateReservesEnabled
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
        validate_compatibility_parameters_against_version(study.version, parameters)

        commands: list[ICommand] = []
        if parameters.hydro_pmax is not None:
            commands.append(
                ConvertHydroPmax(
                    hydro_pmax=parameters.hydro_pmax,
                    command_context=self._command_context,
                    study_version=study.version,
                )
            )
        if parameters.reserves_enabled is not None:
            commands.append(
                UpdateReservesEnabled(
                    reserves_enabled=parameters.reserves_enabled,
                    command_context=self._command_context,
                    study_version=study.version,
                )
            )

        if commands:
            study.add_commands(commands)
        return self.get_compatibility_parameters(study)
