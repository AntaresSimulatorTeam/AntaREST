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

import enum
import typing

from typing_extensions import override


class EnumIgnoreCase(enum.StrEnum):
    """
    Case-insensitive enum base class

    Usage:

    >>> class WeekDay(EnumIgnoreCase):
    ...     MONDAY = "Monday"
    ...     TUESDAY = "Tuesday"
    ...     WEDNESDAY = "Wednesday"
    ...     THURSDAY = "Thursday"
    ...     FRIDAY = "Friday"
    ...     SATURDAY = "Saturday"
    ...     SUNDAY = "Sunday"
    >>> WeekDay("monday")
    <WeekDay.MONDAY: 'Monday'>
    >>> WeekDay("MONDAY")
    <WeekDay.MONDAY: 'Monday'>
    """

    @classmethod
    @override
    def _missing_(cls, value: object) -> typing.Optional["EnumIgnoreCase"]:
        if isinstance(value, str):
            for member in cls:
                # noinspection PyUnresolvedReferences
                if member.value.upper() == value.upper():
                    # noinspection PyTypeChecker
                    return member
        # `value` is not a valid
        return None
