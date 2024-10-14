# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import typing as t

from antares.study.version import StudyVersion

from antarest.study.business.thematic_trimming_field_infos import (
    ThematicTrimmingFormFieldsType,
    create_thematic_trimming_config,
    get_fields_info,
    get_thematic_trimming_cls,
)
from antarest.study.business.utils import GENERAL_DATA_PATH, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class ThematicTrimmingManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> ThematicTrimmingFormFieldsType:
        """
        Get Thematic Trimming field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        config = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        trimming_config = config.get("variables selection") or {}
        exclude_vars = trimming_config.get("select_var -") or []
        include_vars = trimming_config.get("select_var +") or []
        selected_vars_reset = trimming_config.get("selected_vars_reset", True)

        def get_value(field_info: t.Mapping[str, t.Any]) -> bool:
            if selected_vars_reset is None:
                return t.cast(bool, field_info["default_value"])
            var_name = field_info["path"]
            return var_name not in exclude_vars if selected_vars_reset else var_name in include_vars

        fields_info = get_fields_info(StudyVersion.parse(study.version))
        fields_values = {name: get_value(info) for name, info in fields_info.items()}
        return create_thematic_trimming_config(StudyVersion.parse(study.version), **fields_values)

    def set_field_values(self, study: Study, field_values: ThematicTrimmingFormFieldsType) -> None:
        """
        Set Thematic Trimming config from the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        cls = get_thematic_trimming_cls(StudyVersion.parse(study.version))
        field_values_dict = cls.model_validate(field_values).model_dump()

        keys_by_bool: t.Dict[bool, t.List[t.Any]] = {True: [], False: []}
        fields_info = get_fields_info(StudyVersion.parse(study.version))
        for name, info in fields_info.items():
            keys_by_bool[field_values_dict[name]].append(info["path"])

        config_data: t.Dict[str, t.Any]
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

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateConfig(
                    target="settings/generaldata/variables selection",
                    data=config_data,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
