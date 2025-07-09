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

from typing import List

from antarest.study.business.model.config.general_model import (
    GENERAL_PATH,
    BuildingMode,
    GeneralConfig,
    GeneralConfigUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
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
        # commands.extend(self.__get_building_mode_update_cmds(value, study, cmd_cx))
        study.add_commands(commands)

    def __get_building_mode_update_cmds(
        self,
        new_value: BuildingMode,
        study: StudyInterface,
        cmd_context: CommandContext,
    ) -> List[UpdateConfig]:
        if new_value == BuildingMode.DERATED:
            return [
                UpdateConfig(
                    target=f"{GENERAL_PATH}/derated",
                    data=True,
                    command_context=cmd_context,
                    study_version=study.version,
                )
            ]

        return [
            UpdateConfig(
                target=(
                    f"{GENERAL_PATH}/custom-scenario"
                    if study.version >= STUDY_VERSION_8
                    else f"{GENERAL_PATH}/custom-ts-numbers"
                ),
                data=new_value == BuildingMode.CUSTOM,
                command_context=cmd_context,
                study_version=study.version,
            ),
            UpdateConfig(
                target=f"{GENERAL_PATH}/derated", data=False, command_context=cmd_context, study_version=study.version
            ),
        ]
