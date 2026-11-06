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

import pytest

from antarest.study.business.model.gems.calendar import GemsCalendar, _GemsCalendarData
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

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
SAMPLE_CSV_BYTES = b"absolute_time_index,block,granular_date\n0,0,2025-01-01 00:00:00\n1,0,2025-01-01 01:00:00\n"


def test_filestudy_gems_calendar_dao(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # Initially does not exist
    assert filestudy_dao_v10_2.get_gems_calendar() is None

    # Save valid calendar
    filestudy_dao_v10_2.save_gems_calendar(SAMPLE_CALENDAR)
    assert filestudy_dao_v10_2.get_gems_calendar() == SAMPLE_CALENDAR

    # Check file exists on filesystem at input/calendar_file.csv
    study_path = filestudy_dao_v10_2.get_file_study().config.study_path
    calendar_file = study_path / "input" / "calendar_file.csv"
    assert calendar_file.exists()
    assert calendar_file.read_bytes() == SAMPLE_CSV_BYTES

    # Corrupted file on filesystem causes ValueError on read
    calendar_file.write_bytes(b"absolute_time_index,block,granular_date\n0,0,invalid-date\n")
    with pytest.raises(ValueError, match="Invalid date"):
        filestudy_dao_v10_2.get_gems_calendar()
