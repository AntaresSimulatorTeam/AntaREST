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

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.calendar import GemsCalendar, _GemsCalendarData
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.calendar import GEMS_CALENDAR_TABLE
from tests.study.dao.conftest import build_db_dao_10_2

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


def test_gems_calendar_dao(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    first = build_db_dao_10_2(db_session, matrix_service)
    second = build_db_dao_10_2(db_session, matrix_service)

    # Initial state: None
    assert first.get_gems_calendar() is None
    assert second.get_gems_calendar() is None

    # Save calendar
    first.save_gems_calendar(SAMPLE_CALENDAR)
    second.save_gems_calendar(OTHER_CALENDAR)

    assert first.get_gems_calendar() == SAMPLE_CALENDAR
    assert second.get_gems_calendar() == OTHER_CALENDAR

    # Verify directly in DB
    table = GEMS_CALENDAR_TABLE
    study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first.get_study_id())
    )
    row = db_session.execute(select(table).where(table.c.study_data_id == study_data_id)).fetchone()
    assert row is not None
    assert bytes(row.calendar) == SAMPLE_CALENDAR.model_dump_json().encode("utf-8")

    # Replace calendar
    replacement = GemsCalendar(
        data=[
            _GemsCalendarData(
                absolute_time_index=0,
                block=0,
                granular_date=datetime(2025, 6, 1, 12, 0, 0),
            ),
        ]
    )
    first.save_gems_calendar(replacement)
    assert first.get_gems_calendar() == replacement
    assert second.get_gems_calendar() == OTHER_CALENDAR

    # Cascading delete when study_data is deleted
    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == study_data_id))
    db_session.commit()
    assert first.get_gems_calendar() is None
    assert second.get_gems_calendar() == OTHER_CALENDAR
