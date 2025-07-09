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
from abc import ABC, abstractmethod
from typing import Any, Dict, cast

from typing_extensions import override

from antarest.study.business.model.config.general_model import (
    BUILDING_MODE,
    FIELDS_INFO,
    GENERAL,
    GENERAL_PATH,
    OUTPUT,
    BuildingMode,
    GeneralConfig,
)
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo
from antarest.study.dao.api.general_config_dao import GeneralConfigDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyGeneralConfigDao(GeneralConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_general_config(self) -> GeneralConfig:
        def __get_building_mode_value(general_config: Dict[str, Any]) -> str:
            if general_config.get("derated", False):
                return BuildingMode.DERATED.value

            # 'custom-scenario' replaces 'custom-ts-numbers' in study versions >= 800
            if general_config.get("custom-scenario", False) or general_config.get("custom-ts-numbers", False):
                return BuildingMode.CUSTOM.value

            return str(FIELDS_INFO[BUILDING_MODE]["default_value"])

        """
        Get General field values for the webapp form
        """
        file_study = self.get_file_study()
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        general = general_data.get(GENERAL, {})
        output = general_data.get(OUTPUT, {})

        def get_value(field_name: str, field_info: FieldInfo) -> Any:
            if field_name == BUILDING_MODE:
                return __get_building_mode_value(general)
            path = field_info["path"]
            study_ver = file_study.config.version
            start_ver = cast(int, field_info.get("start_version", 0))
            end_ver = cast(int, field_info.get("end_version", study_ver))
            target_name = path.split("/")[-1]
            is_in_version = start_ver <= study_ver <= end_ver
            parent = general if GENERAL_PATH in path else output

            return parent.get(target_name, field_info["default_value"]) if is_in_version else None

        return GeneralConfig.model_construct(**{name: get_value(name, info) for name, info in FIELDS_INFO.items()})

    @override
    def update_general_config(self, config: GeneralConfig) -> None:
        pass
