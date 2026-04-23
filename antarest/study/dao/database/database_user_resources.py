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

from pathlib import PurePosixPath

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import UserResourcesNotFound
from antarest.study.business.model.user_model import UserResourceDataCreation
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple


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

    @override
    def save_user_resources(self, resource_data: list[UserResourceDataCreation]) -> None:
        values = []
        for resource in resource_data:
            values.append(
                {
                    "study_id": self._study_id,
                    "path": str(resource.path),
                    "resource_type": resource.resource_type,
                    "blob_id": resource.blob_id,
                }
            )
        upsert_multiple(self._db_session, USER_RESOURCES_TABLE, values)

        self._db_session.commit()

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        stmt = delete(USER_RESOURCES_TABLE).where(
            (USER_RESOURCES_TABLE.c.study_id == self._study_id) & (USER_RESOURCES_TABLE.c.path == str(resource_path))
        )

        result = self._db_session.execute(stmt)

        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            raise UserResourcesNotFound(str(resource_path))

        self._db_session.commit()

    @override
    def get_all_user_resources(self) -> list[UserResourceDataCreation]:
        stmt = select(USER_RESOURCES_TABLE).where(USER_RESOURCES_TABLE.c.study_id == self._study_id)

        rows = self._db_session.execute(stmt).fetchall()

        return [
            UserResourceDataCreation(path=PurePosixPath(row.path), resource_type=row.resource_type, blob_id=row.blob_id)
            for row in rows
        ]
