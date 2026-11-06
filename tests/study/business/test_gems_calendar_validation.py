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

import pytest

from antarest.study.dao.api.gems_calendar_dao import validate_gems_calendar


def test_validate_gems_calendar_valid() -> None:
    csv_content = (
        b"absolute_time_index,block,granular_date\n"
        b"0,0,2025-01-01 00:00:00\n"
        b"1,0,2025-01-01 01:00:00\n"
        b"2,0,2025-01-01 02:00:00\n"
    )
    validate_gems_calendar(csv_content)


def test_validate_gems_calendar_valid_with_whitespace() -> None:
    csv_content = b"absolute_time_index, block , granular_date \n0, 0, 2025-01-01 00:00:00 \n"
    validate_gems_calendar(csv_content)


def test_validate_gems_calendar_empty() -> None:
    with pytest.raises(ValueError, match="empty or missing a header"):
        validate_gems_calendar(b"")


def test_validate_gems_calendar_missing_granular_date_column() -> None:
    csv_content = b"absolute_time_index,block,date\n0,0,2025-01-01 00:00:00\n"
    with pytest.raises(ValueError, match="must contain a 'granular_date' column"):
        validate_gems_calendar(csv_content)


@pytest.mark.parametrize(
    "invalid_date",
    [
        "2025-01-01",
        "2025-01-01 00:00",
        "2025-01-01 00:00:00+01:00",
        "2025-01-01T00:00:00",
        "01/01/2025 00:00:00",
        "2025-02-29 00:00:00",  # 2025 is not a leap year
        "2025-13-01 00:00:00",  # invalid month
        "2025-01-32 00:00:00",  # invalid day
        "2025-01-01 25:00:00",  # invalid hour
        "not-a-date",
        "",
    ],
)
def test_validate_gems_calendar_invalid_date(invalid_date: str) -> None:
    csv_content = f"absolute_time_index,block,granular_date\n0,0,{invalid_date}\n".encode("utf-8")
    with pytest.raises(ValueError, match="Invalid date"):
        validate_gems_calendar(csv_content)


def test_validate_gems_calendar_non_utf8() -> None:
    with pytest.raises(ValueError, match="not valid UTF-8"):
        validate_gems_calendar(b"\xff\xfe\x00\x00")
