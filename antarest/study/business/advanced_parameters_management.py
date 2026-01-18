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


from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters, AdvancedParametersUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.hydro_pmax_converter import HydroPmaxConverter
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_advanced_parameters import UpdateAdvancedParameters
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AdvancedParamsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_advanced_parameters(self, study: StudyInterface) -> AdvancedParameters:
        """
        Get Advanced parameters values for the webapp form
        """
        return study.get_study_dao().get_advanced_parameters()

    def update_advanced_parameters(
        self, study: StudyInterface, parameters: AdvancedParametersUpdate
    ) -> AdvancedParameters:
        """
        Update Advanced parameters values from the webapp form
        """
        current_parameters = self.get_advanced_parameters(study)

        # Check if hydro_pmax actually changed
        hydro_pmax_changed = (
            parameters.hydro_pmax is not None and current_parameters.hydro_pmax != parameters.hydro_pmax
        )

        commands: list[ICommand] = []

        commands.append(
            UpdateAdvancedParameters(
                command_context=self._command_context, study_version=study.version, parameters=parameters
            )
        )

        if hydro_pmax_changed:
            commands.append(
                HydroPmaxConverter(
                    command_context=self._command_context,
                    study_version=study.version,
                    hydro_pmax=parameters.hydro_pmax,
                )
            )

        study.add_commands(commands)
        return self.get_advanced_parameters(study)
