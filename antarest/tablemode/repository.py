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

from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import get_user_impersonator
from antarest.tablemode.model import TableMode


class TablemodeRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def get_all(self) -> Sequence[TableMode]:
        stmt = select(TableMode).where(TableMode.user_id == get_user_impersonator())
        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def save(self, tablemode: TableMode) -> TableMode:
        session = self.session
        session.add(tablemode)
        session.commit()

        return tablemode

    def get(self, tablemode_id: UUID) -> TableMode | None:
        stmt = (
            select(TableMode)
            .where(TableMode.table_id == tablemode_id)
            .where(TableMode.user_id == get_user_impersonator())
        )
        result = self.session.execute(stmt)
        return result.unique().scalar()

    def delete(self, tablemode_id: UUID) -> None:
        session = self.session
        stmt = (
            delete(TableMode)
            .where(TableMode.user_id == get_user_impersonator())
            .where(TableMode.table_id == tablemode_id)
        )
        session.execute(stmt)
        session.commit()
