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
from typing import Any, Dict

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.config.general_model import (
    BuildingMode,
    DayNumberType,
    GeneralConfig,
    Month,
    WeekDay,
    initialize_default_values,
    validate_general_config_version,
)
from antarest.study.model import STUDY_VERSION_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode


class GeneralFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    mode: Mode | None = Field(default=None)
    first_day: DayNumberType | None = Field(default=None, alias="simulation.start")
    last_day: DayNumberType | None = Field(default=None, alias="simulation.end")
    horizon: str | int | None = Field(default=None)
    first_month: Month | None = Field(default=None, alias="first-month-in-year")
    first_week_day: WeekDay | None = Field(default=None, alias="first.weekday")
    first_january: WeekDay | None = Field(default=None, alias="january.1st")
    leap_year: bool | None = Field(default=None, alias="leapyear")
    nb_years: int | None = Field(default=None, alias="nbyears")
    building_mode: BuildingMode | None = Field(default=None)
    selection_mode: bool | None = Field(default=None, alias="user-playlist")
    year_by_year: bool | None = Field(default=None, alias="year-by-year")
    simulation_synthesis: bool | None = Field(default=None, alias="synthesis")
    mc_scenario: bool | None = Field(default=None, alias="storenewset")
    filtering: bool | None = Field(default=None)
    geographic_trimming: bool | None = Field(default=None, alias="geographic-trimming")
    thematic_trimming: bool | None = Field(default=None, alias="thematic-trimming")
    derated: bool | None = Field(default=None)
    custom_scenario: bool | None = Field(default=None, alias="custom-scenario")
    custom_ts_numbers: bool | None = Field(default=None, alias="custom-ts-numbers")

    def to_model(self) -> GeneralConfig:
        data = self.model_dump(exclude_none=True, exclude={"derated", "custom_scenario", "custom_ts_numbers"})
        if self.derated is True:
            data["building_mode"] = BuildingMode.DERATED
        elif self.custom_scenario is True:
            data["building_mode"] = BuildingMode.CUSTOM
        elif self.custom_ts_numbers is True:
            data["building_mode"] = BuildingMode.CUSTOM
        return GeneralConfig.model_validate(data)

    @classmethod
    def from_model(cls, config: GeneralConfig, study_version: StudyVersion) -> "GeneralFileData":
        data = config.model_dump(exclude={"id"})
        if config.building_mode == BuildingMode.DERATED:
            data["derated"] = True
        else:
            data["derated"] = False
            if study_version >= STUDY_VERSION_8:
                data["custom_scenario"] = config.building_mode == BuildingMode.CUSTOM
            else:
                data["custom_ts_numbers"] = config.building_mode == BuildingMode.CUSTOM
        return cls.model_validate(data)


def parse_general_config(data: Dict[str, Any], version: StudyVersion) -> GeneralConfig:
    config_data = data.get("general", {})
    config_data.update(data.get("output", {}))
    config = GeneralFileData.model_validate(config_data).to_model()
    validate_general_config_version(config, version)
    initialize_default_values(config, version)
    return config


def serialize_simulation_config(config: GeneralConfig, study_version: StudyVersion) -> Dict[str, Any]:
    file_data = GeneralFileData.from_model(config, study_version)
    data = file_data.model_dump(by_alias=True, exclude_none=True, exclude={"simulation_synthesis", "mc_scenario"})
    if "building_mode" in data:
        data["building_mode"] = data["building_mode"].lower()
    return data


def serialize_output_config(config: GeneralConfig, study_version: StudyVersion) -> Dict[str, Any]:
    file_data = GeneralFileData.from_model(config, study_version)
    return file_data.model_dump(by_alias=True, exclude_none=True, include={"simulation_synthesis", "mc_scenario"})
