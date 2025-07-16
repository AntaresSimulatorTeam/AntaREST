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
from typing import Any, Dict, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, PositiveInt, StrictBool

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.config.general_model import (
    BuildingMode,
    DayNumberType,
    GeneralConfig,
    Month,
    WeekDay,
)
from antarest.study.model import STUDY_VERSION_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode


class GeneralFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode: Optional[Mode] = Field(default=None)
    first_day: Optional[DayNumberType] = Field(default=None, alias="simulation.start")
    last_day: Optional[DayNumberType] = Field(default=None, alias="simulation.end")
    horizon: Optional[str | int] = Field(default=None)
    first_month: Optional[Month] = Field(default=None, alias="first-month-in-year")
    first_week_day: Optional[WeekDay] = Field(default=None, alias="first.weekday")
    first_january: Optional[WeekDay] = Field(default=None, alias="january.1st")
    leap_year: Optional[StrictBool] = Field(default=None, alias="leapyear")
    nb_years: Optional[PositiveInt] = Field(default=None, alias="nbyears")
    building_mode: Optional[BuildingMode] = Field(default=None)
    selection_mode: Optional[StrictBool] = Field(default=None, alias="user-playlist")
    year_by_year: Optional[StrictBool] = Field(default=None, alias="year-by-year")
    simulation_synthesis: Optional[StrictBool] = Field(default=None, alias="synthesis")
    mc_scenario: Optional[StrictBool] = Field(default=None, alias="storenewset")
    filtering: Optional[StrictBool] = Field(default=None)
    geographic_trimming: Optional[StrictBool] = Field(default=None, alias="geographic-trimming")
    thematic_trimming: Optional[StrictBool] = Field(default=None, alias="thematic-trimming")
    derated: Optional[StrictBool] = Field(default=None)
    custom_scenario: Optional[StrictBool] = Field(default=None, alias="custom-scenario")
    custom_ts_numbers: Optional[StrictBool] = Field(default=None, alias="custom-ts-numbers")

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


def serialize_simulation_config(config: GeneralConfig, study_version: StudyVersion) -> Dict[str, Any]:
    file_data = GeneralFileData.from_model(config, study_version)
    return file_data.model_dump(by_alias=True, exclude_none=True, exclude={"simulation_synthesis", "mc_scenario"})


def serialize_output_config(config: GeneralConfig, study_version: StudyVersion) -> Dict[str, Any]:
    file_data = GeneralFileData.from_model(config, study_version)
    return file_data.model_dump(by_alias=True, exclude_none=True, include={"simulation_synthesis", "mc_scenario"})
