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

import datetime
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from antarest.study.model import (
    MatrixFrequency,
    MatrixIndex,
)
from antarest.study.storage.utils import DAY_NAMES, get_start_date


@pytest.mark.parametrize(
    "config,level,expected",
    [
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": True,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2024, 1, 1)),
                steps=51,
                first_week_size=7,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2018, 1, 1)),
                steps=51,
                first_week_size=7,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Wednesday",
                "simulation.start": 5,
                "simulation.end": 340,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 5)),
                steps=48,
                first_week_size=7,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 200,
            },
            MatrixFrequency.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=7,
                first_week_size=2,
                level=MatrixFrequency.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 100,
            },
            MatrixFrequency.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=4,
                first_week_size=2,
                level=MatrixFrequency.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            MatrixFrequency.HOURLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 5)),
                steps=2304,
                first_week_size=1,
                level=MatrixFrequency.HOURLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            MatrixFrequency.ANNUAL,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 5)),
                steps=1,
                first_week_size=1,
                level=MatrixFrequency.ANNUAL,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Sunday",
                "leapyear": False,
                "first.weekday": "Friday",
                "simulation.start": 3,
                "simulation.end": 100,
            },
            MatrixFrequency.DAILY,
            MatrixIndex(
                start_date=str(datetime.datetime(2022, 3, 3)),
                steps=98,
                first_week_size=1,
                level=MatrixFrequency.DAILY,
            ),
        ),
    ],
)
def test_create_matrix_index_output(config: Dict[str, Any], level: MatrixFrequency, expected: MatrixIndex) -> None:
    config_mock = Mock()
    config_mock.archived = False
    output_id = "some output"

    file_study = Mock()
    file_study.tree.get.return_value = {"general": config}
    file_study.config.outputs = {output_id: config_mock}

    assert get_start_date(file_study, output_id, level) == expected


@pytest.mark.parametrize(
    "config,level,expected",
    [
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": True,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2024, 1, 1)),
                steps=53,
                first_week_size=7,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "january",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 354,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2018, 1, 1)),
                steps=53,
                first_week_size=7,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Wednesday",
                "simulation.start": 5,
                "simulation.end": 340,
            },
            MatrixFrequency.WEEKLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=53,
                first_week_size=4,
                level=MatrixFrequency.WEEKLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 200,
            },
            MatrixFrequency.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=12,
                first_week_size=2,
                level=MatrixFrequency.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "july",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 1,
                "simulation.end": 100,
            },
            MatrixFrequency.MONTHLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 7, 1)),
                steps=12,
                first_week_size=2,
                level=MatrixFrequency.MONTHLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            MatrixFrequency.HOURLY,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 1)),
                steps=8760,
                first_week_size=5,
                level=MatrixFrequency.HOURLY,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Monday",
                "leapyear": False,
                "first.weekday": "Monday",
                "simulation.start": 5,
                "simulation.end": 100,
            },
            MatrixFrequency.ANNUAL,
            MatrixIndex(
                start_date=str(datetime.datetime(2028, 3, 1)),
                steps=1,
                first_week_size=5,
                level=MatrixFrequency.ANNUAL,
            ),
        ),
        (
            {
                "first-month-in-year": "march",
                "january.1st": "Sunday",
                "leapyear": False,
                "first.weekday": "Friday",
                "simulation.start": 3,
                "simulation.end": 100,
            },
            MatrixFrequency.DAILY,
            MatrixIndex(
                start_date=str(datetime.datetime(2022, 3, 1)),
                steps=365,
                first_week_size=3,
                level=MatrixFrequency.DAILY,
            ),
        ),
    ],
)
def test_create_matrix_index_input(config: Dict[str, Any], level: MatrixFrequency, expected: MatrixIndex) -> None:
    file_study = Mock()
    file_study.tree.get.return_value = {"general": config}
    # Asserts the content are the same
    actual = get_start_date(file_study, None, level)
    assert actual == expected
    # Asserts the returned 1st January corresponds to the chosen one
    actual_datetime = datetime.datetime.strptime(actual.start_date, "%Y-%m-%d %H:%M:%S")
    next_year = str(actual_datetime.year + (actual_datetime.month != 1))
    first_january = datetime.datetime.strptime(next_year, "%Y").weekday()
    assert first_january == DAY_NAMES.index(config["january.1st"])
