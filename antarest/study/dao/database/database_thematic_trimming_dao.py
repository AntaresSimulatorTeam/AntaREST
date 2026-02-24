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

from abc import abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import StudyNotFoundError
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.dao.api.thematic_trimming_dao import ThematicTrimmingDao
from antarest.study.dao.database.models.thematic_trimming import THEMATIC_TRIMMING_TABLE
from antarest.study.dao.database.sql_utils import upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseThematicTrimmingDao(ThematicTrimmingDao):
    """Database implementation of ThematicTrimmingDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(THEMATIC_TRIMMING_TABLE).where((THEMATIC_TRIMMING_TABLE.c.study_id == study_id))

        row = session.execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return ThematicTrimming.model_validate(row.thematic_trimming)

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        session = self.get_session()
        values = {"study_id": self.get_study_id(), "thematic_trimming": trimming.model_dump(exclude_none=True)}

        try:
            upsert_one(session, THEMATIC_TRIMMING_TABLE, values)
        except IntegrityError:
            # Happens if the study does not exist -> ForeignKey constraint fails
            raise StudyNotFoundError(self.get_study_id())

        session.commit()
