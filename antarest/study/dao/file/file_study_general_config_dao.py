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
from typing import Any, Dict

from typing_extensions import override

from antarest.study.business.model.config.general_model import (
    GENERAL,
    OUTPUT,
    BuildingMode,
    GeneralConfig,
)
from antarest.study.business.utils import GENERAL_DATA_PATH
from antarest.study.dao.api.general_config_dao import GeneralConfigDao
from antarest.study.model import STUDY_VERSION_7_1, STUDY_VERSION_8
from antarest.study.storage.rawstudy.model.filesystem.config.general import get_general_config, get_output_config
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyGeneralConfigDao(GeneralConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_general_config(self) -> GeneralConfig:
        def __get_building_mode_value(general_config: Dict[str, Any]) -> BuildingMode:
            if general_config.get("derated", False):
                return BuildingMode.DERATED
            # 'custom-scenario' replaces 'custom-ts-numbers' in study versions >= 800
            if general_config.get("custom-scenario", False) or general_config.get("custom-ts-numbers", False):
                return BuildingMode.CUSTOM
            return BuildingMode.AUTOMATIC

        file_study = self.get_file_study()
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        general = general_data.get(GENERAL, {})
        output = general_data.get(OUTPUT, {})
        study_ver = file_study.config.version

        config_values: Dict[str, Any] = {
            "mode": general.get("mode"),
            "first_day": general.get("simulation.start"),
            "last_day": general.get("simulation.end"),
            "horizon": general.get("horizon"),
            "first_month": general.get("first-month-in-year"),
            "first_week_day": general.get("first.weekday"),
            "first_january": general.get("january.1st"),
            "leap_year": general.get("leapyear"),
            "nb_years": general.get("nbyears"),
            "building_mode": __get_building_mode_value(general),
            "selection_mode": general.get("user-playlist"),
            "year_by_year": general.get("year-by-year"),
            "simulation_synthesis": output.get("synthesis"),
            "mc_scenario": output.get("storenewset"),
        }

        if study_ver <= STUDY_VERSION_7_1:
            config_values["filtering"] = general.get("filtering")

        if study_ver >= STUDY_VERSION_7_1:
            config_values["geographic_trimming"] = general.get("geographic-trimming")
            config_values["thematic_trimming"] = general.get("thematic-trimming")

        return GeneralConfig.model_validate({k: v for k, v in config_values.items() if v is not None})

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        study_data = self.get_file_study()

        current_general_config = study_data.tree.get(["settings", "generaldata", "general"])
        general_config = get_general_config(config)
        general_config = self.update_building_mode(general_config)
        general_config.update({k: v for k, v in current_general_config.items() if k not in general_config})
        study_data.tree.save(general_config, ["settings", "generaldata", "general"])

        current_output_config = study_data.tree.get(["settings", "generaldata", "output"])
        general_output = get_output_config(config)
        general_output.update({k: v for k, v in current_output_config.items() if k not in general_output})
        study_data.tree.save(general_output, ["settings", "generaldata", "output"])

    def update_building_mode(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if config.get("building_mode", "") == BuildingMode.DERATED:
            config.update({"derated": True})
        else:
            config.update({"derated": False})
            if self.get_file_study().config.version >= STUDY_VERSION_8:
                config.update({"custom-scenario": BuildingMode.CUSTOM == config.get("building_mode", "")})
            else:
                config.update({"custom-ts-numbers": BuildingMode.CUSTOM == config.get("building_mode", "")})
        return config
