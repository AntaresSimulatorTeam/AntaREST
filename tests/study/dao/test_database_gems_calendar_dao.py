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
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.calendar import GEMS_CALENDAR_TABLE
from tests.study.dao.conftest import build_db_dao_10_2

SAMPLE_CALENDAR = b"absolute_time_index,block,granular_date\n0,0,2025-01-01 00:00:00\n1,0,2025-01-01 01:00:00\n"
OTHER_CALENDAR = b"absolute_time_index,block,granular_date\n0,0,2026-01-01 00:00:00\n"


def test_database_gems_calendar_dao(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
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
    assert bytes(row.calendar) == SAMPLE_CALENDAR

    # Replace calendar
    replacement = b"absolute_time_index,block,granular_date\n0,0,2025-06-01 12:00:00\n"
    first.save_gems_calendar(replacement)
    assert first.get_gems_calendar() == replacement
    assert second.get_gems_calendar() == OTHER_CALENDAR

    # Validation failure does not save invalid calendar
    with pytest.raises(ValueError, match="Invalid date"):
        first.save_gems_calendar(b"absolute_time_index,block,granular_date\n0,0,bad-date\n")
    assert first.get_gems_calendar() == replacement

    # Cascading delete when study_data is deleted
    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == study_data_id))
    db_session.commit()
    assert first.get_gems_calendar() is None
    assert second.get_gems_calendar() == OTHER_CALENDAR
