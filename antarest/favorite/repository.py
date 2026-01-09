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
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.model import Favorite
from antarest.login.model import User
from antarest.login.utils import get_user_id
from antarest.study.model import Study


class FavoriteRepository:
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def save(self, favorite: Favorite) -> Favorite:
        session = self.session
        fav = session.merge(favorite)
        session.add(fav)
        session.commit()
        return fav

    def get_all(self) -> list[Favorite]:
        stmt = (
            select(Favorite)
            .options(joinedload(Favorite.study))
            .where((Study.id == Favorite.study_id) & (User.id == get_user_id()))
        )
        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def delete(self, user_id: str, study_id: str) -> None:
        session = self.session
        stmt = delete(Favorite).where(Favorite.user_id == user_id).where(Favorite.study_id == study_id)
        session.execute(stmt)
        session.commit()
