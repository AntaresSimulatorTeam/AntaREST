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
Database implementation of UserResourcesDao.
"""

from abc import abstractmethod
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Iterator

from sqlalchemy import select, CursorResult, delete
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import UserResourcesNotFound
from antarest.study.business.model.user_model import UserResourceDataCreation
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE
from antarest.study.dao.database.sql_utils import upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseUserResourcesDao(UserResourcesDao):
    """Database implementation of UserResourcesDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseUserResourcesDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
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
    def save_user_resource(self, resource_data: UserResourceDataCreation) -> None:
        study_id = self._study_id
        session = self._db_session

        values = {
            "study_id": study_id,
            "path": str(resource_data.path),
            "resource_type": resource_data.resource_type,
            "blob_id": resource_data.blob_id,
        }
        upsert_one(session, USER_RESOURCES_TABLE, values)

        session.commit()

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = delete(USER_RESOURCES_TABLE).where((USER_RESOURCES_TABLE.c.study_id == study_id) & (USER_RESOURCES_TABLE.c.path == str(resource_path)))

        result = session.execute(stmt)

        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            raise UserResourcesNotFound(str(resource_path))

        session.commit()

    @override
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        stmt = select(USER_RESOURCES_TABLE).where((USER_RESOURCES_TABLE.c.study_id == self._study_id))

        rows = self._db_session.execute(stmt).fetchall()

        for row in rows:
            yield UserResourceDataCreation(
                path=PurePosixPath(row.path), resource_type=row.resource_type, blob_id=row.blob_id
            )
