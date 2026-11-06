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
from abc import ABC, abstractmethod
from datetime import datetime

_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def validate_gems_calendar(calendar_bytes: bytes) -> None:
    """
    Validate that the calendar content is valid CSV and that all dates match
    the GEMS format 'YYYY-MM-DD HH:MM:SS', otherwise raises a ValueError.
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

    for line_num, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) <= date_col_idx:
            raise ValueError(f"Missing date at line {line_num}")
        date_str = row[date_col_idx].strip()
        if not _DATETIME_PATTERN.fullmatch(date_str):
            raise ValueError(
                f"Invalid date format at line {line_num}: {date_str!r}. Expected format is 'YYYY-MM-DD HH:MM:SS'"
            )
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(
                f"Invalid date at line {line_num}: {date_str!r}. Expected format is 'YYYY-MM-DD HH:MM:SS'"
            ) from e


class ReadOnlyGemsCalendarDao(ABC):
    @abstractmethod
    def get_gems_calendar(self) -> bytes | None:
        """Return the GEMS calendar content as binary, or None if not configured."""
        raise NotImplementedError()


class GemsCalendarDao(ReadOnlyGemsCalendarDao):
    @abstractmethod
    def save_gems_calendar(self, calendar: bytes) -> None:
        """Save or replace the GEMS calendar content for the study."""
        raise NotImplementedError()
