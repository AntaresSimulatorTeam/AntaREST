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

from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import StudyNotFoundError
from antarest.study.dao.database.models import STUDY_DATA_TABLE

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
        self._study_data_id: int | None = None

    @property
    def study_id(self) -> str:
        """The study ID, as found in `study.id`."""
        return self._study_id

    @property
    def study_data_id(self) -> int:
        """
        The surrogate key of the study, as found in `study_data.study_data_id`.

        This is the key all study data tables are keyed by. It is resolved lazily, because
        a DAO is built before its `study_data` row exists (see `create_study_dao`), and
        cached, because it is needed by nearly every query.

        Note:
            A context must not outlive the `study_data` row it resolved: deleting the row
            and re-creating it (unarchive, snapshot regeneration, ...) generates a new id,
            and a stale cache would then write into another study's rows. Every such path
            builds a fresh DAO, which is the invariant this cache relies on.
        """
        if self._study_data_id is None:
            stmt = select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == self._study_id)
            study_data_id = self._db_session.execute(stmt).scalar_one_or_none()
            if study_data_id is None:
                raise StudyNotFoundError(self._study_id)
            self._study_data_id = study_data_id
        return self._study_data_id

    def set_study_data_id(self, study_data_id: int) -> None:
        """
        Prime the cache with the id of a freshly inserted `study_data` row, sparing a lookup.
        """
        self._study_data_id = study_data_id

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
    def _study_data_id(self) -> int:
        return self._context.study_data_id

    @property
    def _db_session(self) -> Session:
        return self._context.session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass
