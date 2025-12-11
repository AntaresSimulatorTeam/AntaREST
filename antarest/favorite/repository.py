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
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.model import Favorite


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
        session.add(favorite)
        session.commit()
        return favorite

    def get_all(self) -> Sequence[Favorite]:
        session = self.session
