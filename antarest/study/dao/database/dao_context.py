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

"""
Shared state of the database DAOs.

`DatabaseStudyDao` is composed of one `Database*Dao` mixin per domain. They all need
the same two things: which study they operate on, and the session to query it with.
This module holds that state once, so the study key used to query the study data
tables is defined in a single place.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class StudyDaoContext:
    """
    Identifies the study a set of database DAOs operates on, and carries their session.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    @property
    def study_id(self) -> str:
        """The study ID, as found in `study.id`."""
        return self._study_id

    @property
    def session(self) -> Session:
        """The SQLAlchemy session used for database operations."""
        return self._db_session


class DatabaseDaoBase(ABC):
    """
    Base class of the database DAO mixins, giving them access to the study context.
    """

    def __init__(self, context: StudyDaoContext) -> None:
        self._context = context

    @property
    def _study_id(self) -> str:
        return self._context.study_id

    @property
    def _db_session(self) -> Session:
        return self._context.session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass
