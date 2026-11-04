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
from typing import cast

from sqlalchemy import Table, delete, select, update
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_one
from antarest.output.dbmodel import Output


class OutputRepository:
    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def get(self, study_id: str, output_id: str) -> Output | None:
        stmt = select(Output).where((Output.output_id == output_id) & (Output.study_id == study_id))
        result = self.session.execute(stmt.execution_options(populate_existing=True))
        return result.unique().scalar_one_or_none()

    def get_all(self, study_id: str) -> list[Output]:
        stmt = select(Output).where(Output.study_id == study_id)
        result = self.session.execute(stmt.execution_options(populate_existing=True))
        return list(result.scalars().all())

    def save_unarchiving_date(self, study_id: str, output_id: str, date: datetime) -> None:
        upsert_one(
            self.session,
            cast(Table, Output.__table__),
            {"study_id": study_id, "output_id": output_id, "last_unarchiving_date": date, "disk_space_bytes": None},
        )
        self.session.commit()

    def invalidate_disk_usage(self, study_id: str, output_id: str) -> None:
        self.session.execute(
            update(Output)
            .where(Output.study_id == study_id, Output.output_id == output_id)
            .values(disk_space_bytes=None)
        )
        self.session.commit()

    def save_disk_usage(self, study_id: str, output_id: str, disk_space_bytes: int) -> None:
        upsert_one(
            self.session,
            cast(Table, Output.__table__),
            {"study_id": study_id, "output_id": output_id, "disk_space_bytes": disk_space_bytes},
        )
        self.session.commit()

    def delete(self, study_id: str, output_id: str) -> None:

        session = self.session
        stmt = delete(Output).where(Output.output_id == output_id).where(Output.study_id == study_id)

        session.execute(stmt)
        session.commit()
