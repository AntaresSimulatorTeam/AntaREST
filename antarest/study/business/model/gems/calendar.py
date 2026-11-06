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
from pathlib import Path
from typing import Self

import polars as pl
from polars.exceptions import InvalidOperationError, NoDataError
from pydantic import ConfigDict, Field, field_serializer, model_validator

from antarest.core.serde import AntaresBaseModel

_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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
            first_time_delta = self.data[1].granular_date - self.data[0].granular_date
            for k in range(1, len(self.data) - 1):
                time_delta = self.data[k + 1].granular_date - self.data[k].granular_date
                if time_delta != first_time_delta:
                    raise ValueError("All 'granular_date' must be separated by a constant time step")

        return self

    def write(self, file_path: Path) -> None:
        df = pl.DataFrame(self.data)
        # Write datetime column as string
        df = df.with_columns(pl.col("granular_date").dt.strftime(_DATETIME_FORMAT))
        df.write_csv(file_path, separator=",", include_header=True)

    @classmethod
    def read(cls, file_path: Path) -> "GemsCalendar":
        error_msg = "Calendar file must have these exact columns 'absolute_time_index', 'block', and 'granular_date'"

        try:
            df = pl.read_csv(file_path)
        except NoDataError:
            raise ValueError(error_msg)

        if df.columns != ["absolute_time_index", "block", "granular_date"]:
            raise ValueError(error_msg)

        try:
            df = df.with_columns(pl.col("granular_date").str.to_datetime(_DATETIME_FORMAT).alias("granular_date"))
        except InvalidOperationError:
            raise ValueError(f"Calendar file column 'granular_date' must follow this format: {_DATETIME_FORMAT}")

        return GemsCalendar.model_validate({"data": df.to_dicts()})
