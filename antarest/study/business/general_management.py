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

from typing import Any, Dict, List, cast

from antarest.study.business.model.config.general_model import BuildingMode, GeneralConfig, Month, WeekDay
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo
from antarest.study.model import STUDY_VERSION_7_1, STUDY_VERSION_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

GENERAL = "general"
OUTPUT = "output"
GENERAL_PATH = f"{GENERAL_DATA_PATH}/{GENERAL}"
OUTPUT_PATH = f"{GENERAL_DATA_PATH}/{OUTPUT}"
BUILDING_MODE = "building_mode"

FIELDS_INFO: Dict[str, FieldInfo] = {
    "mode": {
        "path": f"{GENERAL_PATH}/mode",
        "default_value": Mode.ECONOMY.value,
    },
    "first_day": {
        "path": f"{GENERAL_PATH}/simulation.start",
        "default_value": 1,
    },
    "last_day": {
        "path": f"{GENERAL_PATH}/simulation.end",
        "default_value": 365,
    },
    "horizon": {
        "path": f"{GENERAL_PATH}/horizon",
        "default_value": "",
    },
    "first_month": {
        "path": f"{GENERAL_PATH}/first-month-in-year",
        "default_value": Month.JANUARY.value,
    },
    "first_week_day": {
        "path": f"{GENERAL_PATH}/first.weekday",
        "default_value": WeekDay.MONDAY.value,
    },
    "first_january": {
        "path": f"{GENERAL_PATH}/january.1st",
        "default_value": WeekDay.MONDAY.value,
    },
    "leap_year": {
        "path": f"{GENERAL_PATH}/leapyear",
        "default_value": False,
    },
    "nb_years": {
        "path": f"{GENERAL_PATH}/nbyears",
        "default_value": 1,
    },
    BUILDING_MODE: {
        "path": "",
        "default_value": BuildingMode.AUTOMATIC.value,
    },
    "selection_mode": {
        "path": f"{GENERAL_PATH}/user-playlist",
        "default_value": False,
    },
    "year_by_year": {
        "path": f"{GENERAL_PATH}/year-by-year",
        "default_value": False,
    },
    "filtering": {
        "path": f"{GENERAL_PATH}/filtering",
        "default_value": False,
        "end_version": STUDY_VERSION_7_1,
    },
    "geographic_trimming": {
        "path": f"{GENERAL_PATH}/geographic-trimming",
        "default_value": False,
        "start_version": STUDY_VERSION_7_1,
    },
    "thematic_trimming": {
        "path": f"{GENERAL_PATH}/thematic-trimming",
        "default_value": False,
        "start_version": STUDY_VERSION_7_1,
    },
    "simulation_synthesis": {
        "path": f"{OUTPUT_PATH}/synthesis",
        "default_value": True,
    },
    "mc_scenario": {
        "path": f"{OUTPUT_PATH}/storenewset",
        "default_value": False,
    },
}


class GeneralManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface) -> GeneralConfig:
        """
        Get General field values for the webapp form
        """
        file_study = study.get_files()
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        general = general_data.get(GENERAL, {})
        output = general_data.get(OUTPUT, {})

        def get_value(field_name: str, field_info: FieldInfo) -> Any:
            if field_name == BUILDING_MODE:
                return GeneralManager.__get_building_mode_value(general)

            path = field_info["path"]
            study_ver = study.version
            start_ver = cast(int, field_info.get("start_version", 0))
            end_ver = cast(int, field_info.get("end_version", study_ver))
            target_name = path.split("/")[-1]
            is_in_version = start_ver <= study_ver <= end_ver
            parent = general if GENERAL_PATH in path else output

            return parent.get(target_name, field_info["default_value"]) if is_in_version else None

        return GeneralConfig.model_construct(**{name: get_value(name, info) for name, info in FIELDS_INFO.items()})

    def set_field_values(self, study: StudyInterface, field_values: GeneralConfig) -> None:
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
    def __get_building_mode_value(general_config: Dict[str, Any]) -> str:
        if general_config.get("derated", False):
            return BuildingMode.DERATED.value

        # 'custom-scenario' replaces 'custom-ts-numbers' in study versions >= 800
        if general_config.get("custom-scenario", False) or general_config.get("custom-ts-numbers", False):
            return BuildingMode.CUSTOM.value

        return str(FIELDS_INFO[BUILDING_MODE]["default_value"])

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
