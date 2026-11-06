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

import pytest

from antarest.study.business.model.gems.calendar import GemsCalendar, _GemsCalendarData


def test_gems_calendar_model_errors() -> None:
    # Does not start at 0
    with pytest.raises(ValueError, match="All 'absolute_time_index' must make a contiguous list that start at 0"):
        GemsCalendar(
            data=[
                _GemsCalendarData(
                    absolute_time_index=1,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 0, 0, 0),
                ),
            ]
        )

    # Gap in sequence
    with pytest.raises(ValueError, match="All 'absolute_time_index' must make a contiguous list that start at 0"):
        GemsCalendar(
            data=[
                _GemsCalendarData(
                    absolute_time_index=0,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 0, 0, 0),
                ),
                _GemsCalendarData(
                    absolute_time_index=2,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 1, 0, 0),
                ),
            ]
        )

    # Duplicated index
    with pytest.raises(ValueError, match="All 'absolute_time_index' must make a contiguous list that start at 0"):
        GemsCalendar(
            data=[
                _GemsCalendarData(
                    absolute_time_index=0,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 0, 0, 0),
                ),
                _GemsCalendarData(
                    absolute_time_index=0,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 1, 0, 0),
                ),
            ]
        )

    # No constant time-step for `granular_date`
    with pytest.raises(ValueError, match="All 'granular_date' must be separated by a constant time step"):
        GemsCalendar(
            data=[
                _GemsCalendarData(
                    absolute_time_index=0,
                    block=0,
                    granular_date=datetime(2025, 1, 1, 0, 0, 0),
                ),
                _GemsCalendarData(
                    absolute_time_index=1,
                    block=1,
                    granular_date=datetime(2025, 1, 1, 1, 0, 0),
                ),
                _GemsCalendarData(
                    absolute_time_index=2,
                    block=2,
                    granular_date=datetime(2025, 1, 1, 3, 0, 0),
                ),
            ]
        )


@pytest.mark.parametrize(
    "content",
    [
        b"absolute_time_index,block,fake\n0,0,2025-01-01 00:00:00\n",  # No 'granular_date' column
        b"absolute_time_index,fake,granular_date\n0,0,2025-01-01 00:00:00\n",  # No 'block' column
        b"fake,block,granular_date\n0,0,2025-01-01 00:00:00\n",  # No 'absolute_time' column
        b"absolute_time_index,block,granular_date,extra_col\n0,0,2025-01-01 00:00:00,0\n",  # Extra column
        b"granular_date,block,absolute_time_index\n0,0,2025-01-01 00:00:0\n",  # Columns in the wrong order
        b"",  # No columns
        b"absolute_time_index;block;granular_date\n0;0;2025-01-01 00:00:00\n",  # Wrong separator
    ],
)
def test_validate_gems_calendar_columns(content: bytes, tmp_path: Path) -> None:
    file_path = tmp_path / "calendar.csv"
    file_path.write_bytes(content)

    msg = "Calendar file must have these exact columns 'absolute_time_index', 'block', and 'granular_date'"
    with pytest.raises(ValueError, match=msg):
        GemsCalendar.read(file_path)


@pytest.mark.parametrize(
    "invalid_date",
    [
        "2025-01-01",  # Missing hours, minutes and seconds
        "2025-01-01 00:00",  # Missing seconds
        "2025-01-01 00:00:00+01:00",  # No timezone is accepted
        "2025-01-01T00:00:00",  # Wrong format
        "01/01/2025 00:00:00",  # Wrong format
        "2025-13-01 00:00:00",  # invalid month
        "2025-01-32 00:00:00",  # invalid day
        "2025-01-01 25:00:00",  # invalid hour
        "not-a-date",  # Not a date
        "",  # No data
    ],
)
def test_validate_gems_calendar_invalid_date(invalid_date: str, tmp_path: Path) -> None:
    csv_content = f"absolute_time_index,block,granular_date\n0,0,{invalid_date}\n".encode("utf-8")
    file_path = tmp_path / "calendar.csv"
    file_path.write_bytes(csv_content)

    error_msg = "Calendar file column 'granular_date' must follow this format: %Y-%m-%d %H:%M:%S"
    if invalid_date == "":  # Special msg for this case
        error_msg = "1 validation error for GemsCalendar"
    with pytest.raises(ValueError, match=error_msg):
        GemsCalendar.read(file_path)
