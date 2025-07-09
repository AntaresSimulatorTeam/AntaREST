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


from antarest.study.business.model.config.general_model import (
    GeneralConfig,
    GeneralConfigUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_general_config import UpdateGeneralConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class GeneralManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_general_config(self, study: StudyInterface) -> GeneralConfig:
        return study.get_study_dao().get_general_config()

    def update_general_config(self, study: StudyInterface, config: GeneralConfigUpdate) -> None:
        commands = [
            UpdateGeneralConfig(parameters=config, command_context=self._command_context, study_version=study.version)
        ]
        study.add_commands(commands)
