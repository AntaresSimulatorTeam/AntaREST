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
from typing import Optional

from pydantic import ConfigDict, Field, PositiveInt, StrictBool

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.config.general_model import (
    DayNumberType,
    GeneralConfig,
    Month,
    WeekDay,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode


class GeneralFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode: Optional[Mode] = Field(default=None)
    first_day: Optional[DayNumberType] = Field(default=None, alias="simulation.start")
    last_day: Optional[DayNumberType] = Field(default=None, alias="simulation.end")
    horizon: Optional[str | int] = Field(default=None)
    first_month: Optional[Month] = Field(default=None, alias="first-month-in-year")
    first_week_day: Optional[WeekDay] = Field(default=None, alias="first-weekday")
    first_january: Optional[WeekDay] = Field(default=None, alias="january.1st")
    leap_year: Optional[StrictBool] = Field(default=None, alias="leapyear")
    nb_years: Optional[PositiveInt] = Field(default=None, alias="nbyears")
    # building_mode: Optional[BuildingMode] = Field(default=None, alias="")
    selection_mode: Optional[StrictBool] = Field(default=None, alias="user-playlist")
    year_by_year: Optional[StrictBool] = Field(default=None, alias="year-by-year")
    simulation_synthesis: Optional[StrictBool] = Field(default=None, alias="synthesis")
    mc_scenario: Optional[StrictBool] = Field(default=None, alias="storenewset")
    filtering: Optional[StrictBool] = Field(default=None)
    geographic_trimming: Optional[StrictBool] = Field(default=None, alias="geographic-trimming")
    thematic_trimming: Optional[StrictBool] = Field(default=None, alias="thematic-trimming")

    def to_model(self) -> GeneralConfig:
        return GeneralConfig.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, storage: GeneralConfig) -> "GeneralFileData":
        return cls.model_validate(storage.model_dump(exclude={"id"}))
