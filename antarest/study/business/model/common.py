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
from typing import Annotated, TypeAlias

from pydantic import BeforeValidator, PlainSerializer, ValidationError

from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class FilterOption(EnumIgnoreCase):
    """
    Enum representing the time filter options for data visualization or analysis in Antares Web.

    Attributes:
        HOURLY: Represents filtering data by the hour.
        DAILY: Represents filtering data by the day.
        WEEKLY: Represents filtering data by the week.
        MONTHLY: Represents filtering data by the month.
        ANNUAL: Represents filtering data by the year.
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


FILTER_VALUES: list[FilterOption] = [
    FilterOption.HOURLY,
    FilterOption.DAILY,
    FilterOption.WEEKLY,
    FilterOption.MONTHLY,
    FilterOption.ANNUAL,
]


def validate_filters(filter_value: list[FilterOption] | str) -> list[FilterOption]:
    if isinstance(filter_value, str):
        filter_value = filter_value.strip()
        if not filter_value:
            return []

        valid_values = {str(e.value) for e in FilterOption}

        options = filter_value.replace(" ", "").split(",")

        invalid_options = [opt for opt in options if opt not in valid_values]
        if invalid_options:
            raise ValidationError(
                f"Invalid value(s) in filters: {', '.join(invalid_options)}. "
                f"Allowed values are: {', '.join(valid_values)}."
            )
        options_enum: list[FilterOption] = list(dict.fromkeys(FilterOption(opt) for opt in options))
        return options_enum

    return filter_value


def join_with_comma(values: list[FilterOption]) -> str:
    return ", ".join(value.name.lower() for value in values)


CommaSeparatedFilterOptions: TypeAlias = Annotated[
    list[FilterOption],
    BeforeValidator(lambda x: validate_filters(x)),
    PlainSerializer(lambda x: join_with_comma(x)),
]
