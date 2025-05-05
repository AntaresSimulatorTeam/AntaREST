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

from typing import Any, Dict, List, Mapping, cast

from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.thematic_trimming_field_infos import ThematicTrimmingFormFields, get_fields_info
from antarest.study.business.utils import GENERAL_DATA_PATH
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThematicTrimmingManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface) -> ThematicTrimmingFormFields:
        """
        Get Thematic Trimming field values for the webapp form
        """
        file_study = study.get_files()
        config = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        trimming_config = config.get("variables selection") or {}
        exclude_vars = trimming_config.get("select_var -") or []
        include_vars = trimming_config.get("select_var +") or []
        selected_vars_reset = trimming_config.get("selected_vars_reset", True)

        def get_value(field_info: Mapping[str, Any]) -> bool:
            if selected_vars_reset is None:
                return cast(bool, field_info["default_value"])
            var_name = field_info["path"]
            return var_name not in exclude_vars if selected_vars_reset else var_name in include_vars

        fields_info = get_fields_info(study.version)
        fields_values = {name: get_value(info) for name, info in fields_info.items()}
        return ThematicTrimmingFormFields(**fields_values)

    def set_field_values(self, study: StudyInterface, field_values: ThematicTrimmingFormFields) -> None:
        """
        Set Thematic Trimming config from the webapp form
        """
        field_values_dict = field_values.model_dump(mode="json")

        keys_by_bool: Dict[bool, List[Any]] = {True: [], False: []}
        fields_info = get_fields_info(study.version)
        for name, info in fields_info.items():
            keys_by_bool[field_values_dict[name]].append(info["path"])

        config_data: Dict[str, Any]
        if len(keys_by_bool[True]) > len(keys_by_bool[False]):
            config_data = {
                "selected_vars_reset": True,
                "select_var -": keys_by_bool[False],
            }
        else:
            config_data = {
                "selected_vars_reset": False,
                "select_var +": keys_by_bool[True],
            }

        command = UpdateConfig(
            target="settings/generaldata/variables selection",
            data=config_data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
