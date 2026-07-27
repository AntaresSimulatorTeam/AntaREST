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

import uuid
from pathlib import PurePosixPath

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import UserResourcesNotFound
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE


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
            parts = resource.path.parts
            # First part
            first_part = parts[0]
            resource_id = str(uuid.uuid4())
            value = {
                "study_id": self._study_id,
                "id": resource_id,
                "name": first_part,
                "parent_id": None,
                "resource_type": ResourceType.FOLDER,
                "blob_id": None if len(parts) > 1 else resource.blob_id,
            }
            values.append(value)
            # Other parts except the last one
            for part in parts[1 : len(parts) - 1]:
                parent_id = resource_id
                resource_id = str(uuid.uuid4())
                value = {
                    "study_id": self._study_id,
                    "id": resource_id,
                    "name": part,
                    "parent_id": parent_id,
                    "resource_type": ResourceType.FOLDER,
                    "blob_id": None,
                }
                values.append(value)
            # Last part
            if len(parts) > 1:
                last_part = parts[len(parts) - 1]
                value = {
                    "study_id": self._study_id,
                    "id": str(uuid.uuid4()),
                    "name": last_part,
                    "parent_id": resource_id,
                    "resource_type": resource.resource_type,
                    "blob_id": resource.blob_id,
                }
                values.append(value)

        try:
            upsert_multiple(self._db_session, USER_RESOURCES_TABLE, values)
        except IntegrityError as e:
            raise ValueError(f"Could not save user resources {resource_data}") from e

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
