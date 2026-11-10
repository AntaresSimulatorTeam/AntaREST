# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from datetime import datetime
from typing import Self

from pydantic import ConfigDict, Field, field_serializer, model_validator

from antarest.core.serde import AntaresBaseModel

# GEMS supports UTC with time zone offsets, ex: 2025-01-01 00:00:00+01:00
# On our side we do not and assume every given date as an offset of 0.
# If an offset is given, we raise an error.
_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_calendar_datetime_format() -> str:
    return _DATETIME_FORMAT


class _GemsCalendarData(AntaresBaseModel):
    """
    Data entry representing a row of the GEMS calendar.
    """

    model_config = ConfigDict(extra="forbid")

    absolute_time_index: int = Field(ge=0)
    block: int = Field(ge=0)
    granular_date: datetime

    @field_serializer("granular_date")
    def serialize_granular_date(self, v: datetime) -> str:
        return v.strftime(_DATETIME_FORMAT)


class GemsCalendar(AntaresBaseModel):
    """
    Pydantic object representing a GEMS calendar.
    """

    model_config = ConfigDict(extra="forbid")

    data: list[_GemsCalendarData]

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Validate contiguous `absolute_time_index`
        indices = [entry.absolute_time_index for entry in self.data]
        expected = list(range(len(indices)))
        if indices != expected:
            raise ValueError("All 'absolute_time_index' must make a contiguous list that start at 0")

        # Validate constant time step for `granular_date`
        if len(self.data) > 2:
            deltas = (b.granular_date - a.granular_date for a, b in zip(self.data, self.data[1:]))
            first = next(deltas)
            if any(d != first for d in deltas):
                raise ValueError("All 'granular_date' must be separated by a constant time step")

        return self
