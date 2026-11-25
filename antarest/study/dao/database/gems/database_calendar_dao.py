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

from sqlalchemy import select
from typing_extensions import override

from antarest.core.utils.sql_utils import upsert_one
from antarest.study.business.model.gems.calendar import GemsCalendar
from antarest.study.dao.api.gems_calendar_dao import GemsCalendarDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.calendar import GEMS_CALENDAR_TABLE


class DatabaseGemsCalendarDao(GemsCalendarDao, DatabaseDaoBase):
    @override
    def get_gems_calendar(self) -> GemsCalendar | None:
        table = GEMS_CALENDAR_TABLE
        row = self._db_session.execute(select(table).where(table.c.study_data_id == self._study_data_id)).fetchone()
        if not row:
            return None

        return GemsCalendar.model_validate_json(row.calendar)

    @override
    def save_gems_calendar(self, calendar: GemsCalendar) -> None:
        session = self._db_session
        values = {"study_data_id": self._study_data_id, "calendar": calendar.model_dump_json().encode("utf-8")}
        upsert_one(session, GEMS_CALENDAR_TABLE, values)
        session.commit()
