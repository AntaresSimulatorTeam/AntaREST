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


from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters, AdvancedParametersUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AdvancedParamsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_advanced_parameters(self, study: StudyInterface) -> AdvancedParameters:
        """
        Get Advanced parameters values for the webapp form
        """
        return study.get_study_dao().get_advanced_parameters()

    def update_advanced_parameters(self, study: StudyInterface, parameters: AdvancedParametersUpdate) -> None:
        """
        Update Advanced parameters values from the webapp form
        """
        raise NotImplementedError
