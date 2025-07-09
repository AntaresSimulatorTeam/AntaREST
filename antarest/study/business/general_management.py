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
    BUILDING_MODE,
    FIELDS_INFO,
    GENERAL_PATH,
    BuildingMode,
    GeneralConfig,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class GeneralManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_general_config(self, study: StudyInterface) -> GeneralConfig:
        return study.get_study_dao().get_general_config()

    def update_general_config(self, study: StudyInterface, field_values: GeneralConfig) -> None:
        """
        Set Optimization config from the webapp form
        """
        commands: List[UpdateConfig] = []
        cmd_cx = self._command_context

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                if field_name == BUILDING_MODE:
                    commands.extend(GeneralManager.__get_building_mode_update_cmds(value, study, cmd_cx))
                    continue

                commands.append(
                    UpdateConfig(target=info["path"], data=value, command_context=cmd_cx, study_version=study.version)
                )

        if commands:
            study.add_commands(commands)

    @staticmethod
    def __get_building_mode_update_cmds(
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
