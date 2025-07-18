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
from typing import Annotated, Any, Dict, TypeAlias, cast

from pydantic import ConfigDict, Field, PositiveInt, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import GENERAL_DATA_PATH
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode


class Month(EnumIgnoreCase):
    JANUARY = "january"
    FEBRUARY = "february"
    MARCH = "march"
    APRIL = "april"
    MAY = "may"
    JUNE = "june"
    JULY = "july"
    AUGUST = "august"
    SEPTEMBER = "september"
    OCTOBER = "october"
    NOVEMBER = "november"
    DECEMBER = "december"


class WeekDay(EnumIgnoreCase):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class BuildingMode(EnumIgnoreCase):
    AUTOMATIC = "Automatic"
    CUSTOM = "Custom"
    DERATED = "Derated"


DayNumberType: TypeAlias = Annotated[int, Field(ge=1, le=366)]
GENERAL = "general"
OUTPUT = "output"
GENERAL_PATH = f"{GENERAL_DATA_PATH}/{GENERAL}"


class GeneralConfig(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    mode: Mode = Mode.ECONOMY
    first_day: DayNumberType = 1
    last_day: DayNumberType = 365
    horizon: str | int = ""
    first_month: Month = Month.JANUARY
    first_week_day: WeekDay = WeekDay.MONDAY
    first_january: WeekDay = WeekDay.MONDAY
    leap_year: bool = False
    nb_years: PositiveInt = 1
    building_mode: BuildingMode = BuildingMode.AUTOMATIC
    selection_mode: bool = False
    year_by_year: bool = False
    simulation_synthesis: bool = True
    mc_scenario: bool = False
    filtering: bool | None = None
    geographic_trimming: bool | None = None
    thematic_trimming: bool | None = None

    @model_validator(mode="before")
    def day_fields_validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        first_day = values.get("first_day")
        last_day = values.get("last_day")
        leap_year = values.get("leap_year")
        day_fields = [first_day, last_day, leap_year]

        if all(v is None for v in day_fields):
            # The user wishes to update another field than these three.
            # no need to validate anything:
            return values

        if any(v is None for v in day_fields):
            raise ValueError("First day, last day and leap year fields must be defined together")

        first_day = cast(int, first_day)
        last_day = cast(int, last_day)
        leap_year = cast(bool, leap_year)
        num_days_in_year = 366 if leap_year else 365

        if first_day > last_day:
            raise ValueError("Last day must be greater than or equal to the first day")
        if last_day > num_days_in_year:
            raise ValueError(f"Last day cannot be greater than {num_days_in_year}")

        return values


class GeneralConfigUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    mode: Mode | None = None
    first_day: DayNumberType | None = None
    last_day: DayNumberType | None = None
    horizon: str | int | None = None
    first_month: Month | None = None
    first_week_day: WeekDay | None = None
    first_january: WeekDay | None = None
    leap_year: bool | None = None
    nb_years: PositiveInt | None = None
    building_mode: BuildingMode | None = None
    selection_mode: bool | None = None
    year_by_year: bool | None = None
    simulation_synthesis: bool | None = None
    mc_scenario: bool | None = None
    filtering: bool | None = None
    geographic_trimming: bool | None = None
    thematic_trimming: bool | None = None


def update_general_config(config: GeneralConfig, new_config: GeneralConfigUpdate) -> GeneralConfig:
    """
    Updates the general config according to the provided update data.
    """
    current_properties = config.model_dump(mode="json")
    new_properties = new_config.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return GeneralConfig.model_validate(current_properties)
