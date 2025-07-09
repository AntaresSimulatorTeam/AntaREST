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
from typing import Annotated, Any, Dict, Optional, TypeAlias, cast

from pydantic import ConfigDict, Field, PositiveInt, StrictBool, model_validator
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import ValidationInfo

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo
from antarest.study.model import STUDY_VERSION_7_1
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
OUTPUT_PATH = f"{GENERAL_DATA_PATH}/{OUTPUT}"
BUILDING_MODE = "building_mode"


class GeneralConfig(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    mode: Mode = Mode.ECONOMY
    first_day: DayNumberType = 1
    last_day: DayNumberType = 365
    horizon: str | int = ""
    first_month: Month = Month.JANUARY
    first_week_day: WeekDay = WeekDay.MONDAY
    first_january: WeekDay = WeekDay.MONDAY
    leap_year: StrictBool = False
    nb_years: PositiveInt = 1
    building_mode: BuildingMode = BuildingMode.AUTOMATIC
    selection_mode: StrictBool = False
    year_by_year: StrictBool = False
    simulation_synthesis: StrictBool = True
    mc_scenario: StrictBool = False
    filtering: StrictBool = False
    geographic_trimming: StrictBool = False
    thematic_trimming: StrictBool = False

    @model_validator(mode="before")
    def day_fields_validation(cls, values: Dict[str, Any] | ValidationInfo) -> Dict[str, Any]:
        new_values = values if isinstance(values, dict) else values.data
        first_day = new_values.get("first_day")
        last_day = new_values.get("last_day")
        leap_year = new_values.get("leap_year")
        day_fields = [first_day, last_day, leap_year]

        if all(v is None for v in day_fields):
            # The user wishes to update another field than these three.
            # no need to validate anything:
            return new_values

        if any(v is None for v in day_fields):
            raise ValueError("First day, last day and leap year fields must be defined together")

        if new_values.get("filtering") is None:
            new_values["filtering"] = False

        first_day = cast(int, first_day)
        last_day = cast(int, last_day)
        leap_year = cast(bool, leap_year)
        num_days_in_year = 366 if leap_year else 365

        if first_day > last_day:
            raise ValueError("Last day must be greater than or equal to the first day")
        if last_day > num_days_in_year:
            raise ValueError(f"Last day cannot be greater than {num_days_in_year}")

        return new_values


class GeneralConfigUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    mode: Optional[Mode] = None
    first_day: Optional[DayNumberType] = None
    last_day: Optional[DayNumberType] = None
    horizon: Optional[str | int] = None
    first_month: Optional[Month] = None
    first_week_day: Optional[WeekDay] = None
    first_january: Optional[WeekDay] = None
    leap_year: Optional[StrictBool] = None
    nb_years: Optional[PositiveInt] = None
    building_mode: Optional[BuildingMode] = None
    selection_mode: Optional[StrictBool] = None
    year_by_year: Optional[StrictBool] = None
    simulation_synthesis: Optional[StrictBool] = None
    mc_scenario: Optional[StrictBool] = None
    filtering: Optional[StrictBool] = None
    geographic_trimming: Optional[StrictBool] = None
    thematic_trimming: Optional[StrictBool] = None


def update_general_config(config: GeneralConfig, new_config: GeneralConfigUpdate) -> GeneralConfig:
    """
    Updates a link according to the provided update data.
    """
    current_properties = config.model_dump(mode="json")
    new_properties = new_config.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return GeneralConfig.model_validate(current_properties)


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
