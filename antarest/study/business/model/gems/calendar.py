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

import csv
import io
import re
from datetime import datetime
from typing import Any, Self

from pydantic import ConfigDict, field_serializer, field_validator, model_validator

from antarest.core.serde import AntaresBaseModel

_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class _GemsCalendarData(AntaresBaseModel):
    """
    Data entry representing a row of the GEMS calendar.
    """

    model_config = ConfigDict(extra="forbid")

    absolute_time_index: int
    block: int
    granular_date: datetime

    @field_validator("granular_date", mode="before")
    @classmethod
    def validate_granular_date(cls, v: Any) -> datetime:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not _DATETIME_PATTERN.fullmatch(v_stripped):
                raise ValueError(f"Invalid date format: {v!r}. Expected format is '{_DATETIME_FORMAT}'")
            try:
                return datetime.strptime(v_stripped, _DATETIME_FORMAT)
            except ValueError as e:
                raise ValueError(f"Invalid date: {v!r}. Expected format is '{_DATETIME_FORMAT}'") from e
        if isinstance(v, datetime):
            if v.microsecond != 0 or v.tzinfo is not None:
                raise ValueError(
                    f"Invalid date: {v!r}. Expected format is '{_DATETIME_FORMAT}' without microseconds or timezone"
                )
            return v
        raise ValueError(f"Invalid date type: {type(v)}. Expected format is '{_DATETIME_FORMAT}'")

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
    def validate_contiguous_absolute_time_index(self) -> Self:
        indices = [entry.absolute_time_index for entry in self.data]
        expected = list(range(len(indices)))
        if indices != expected:
            raise ValueError("All 'absolute_time_index' must make a contiguous list that start at 0")
        return self

    def to_csv(self) -> bytes:
        """
        Export the calendar data to CSV format as bytes.
        """
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["absolute_time_index", "block", "granular_date"])
        for row in self.data:
            writer.writerow([row.absolute_time_index, row.block, row.granular_date.strftime(_DATETIME_FORMAT)])
        return output.getvalue().encode("utf-8")

    @classmethod
    def from_csv(cls, calendar_bytes: bytes) -> "GemsCalendar":
        """
        Parse and validate a CSV bytes representation of a GEMS calendar.
        """
        try:
            decoded = calendar_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Calendar file is not valid UTF-8: {e}") from e

        reader = csv.reader(io.StringIO(decoded))
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("Calendar file is empty or missing a header row") from None

        cleaned_header = [col.strip() for col in header]
        try:
            date_col_idx = cleaned_header.index("granular_date")
        except ValueError:
            raise ValueError("Calendar file must contain a 'granular_date' column") from None

        try:
            time_idx_col = cleaned_header.index("absolute_time_index")
            block_col = cleaned_header.index("block")
        except ValueError as e:
            raise ValueError(f"Calendar file must contain required columns: {e}") from e

        data: list[_GemsCalendarData] = []
        for line_num, row in enumerate(reader, start=2):
            if not row or not any(field.strip() for field in row):
                continue
            if len(row) <= max(time_idx_col, block_col, date_col_idx):
                raise ValueError(f"Missing column values at line {line_num}")
            data.append(
                _GemsCalendarData(
                    absolute_time_index=int(row[time_idx_col].strip()),
                    block=int(row[block_col].strip()),
                    granular_date=row[date_col_idx].strip(),  # validated by _GemsCalendarData field_validator
                )
            )

        return cls(data=data)
