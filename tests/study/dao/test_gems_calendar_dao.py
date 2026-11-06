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

from antarest.study.business.model.gems.calendar import GemsCalendar, _GemsCalendarData
from antarest.study.dao.api.study_dao import StudyDao

SAMPLE_CALENDAR = GemsCalendar(
    data=[
        _GemsCalendarData(
            absolute_time_index=0,
            block=0,
            granular_date=datetime(2025, 1, 1, 0, 0, 0),
        ),
        _GemsCalendarData(
            absolute_time_index=1,
            block=0,
            granular_date=datetime(2025, 1, 1, 1, 0, 0),
        ),
    ]
)
OTHER_CALENDAR = GemsCalendar(
    data=[
        _GemsCalendarData(
            absolute_time_index=0,
            block=0,
            granular_date=datetime(2026, 1, 1, 0, 0, 0),
        ),
    ]
)


def test_gems_calendar_dao(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    # Initial state: None
    assert dao.get_gems_calendar() is None

    # Save calendar
    dao.save_gems_calendar(SAMPLE_CALENDAR)
    assert dao.get_gems_calendar() == SAMPLE_CALENDAR

    # Replace the calendar
    dao.save_gems_calendar(OTHER_CALENDAR)
    assert dao.get_gems_calendar() == OTHER_CALENDAR
