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
from dataclasses import dataclass
from pathlib import PurePosixPath

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import UserResourcesNotFound
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.api.user_resources_dao import UserResourcesDao
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE

_TABLE = USER_RESOURCES_TABLE


@dataclass(frozen=True)
class UserResourcesDatabaseData:
    ids: list[str]
    blob_id: str | None
    resource_type: ResourceType


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
        tree = self._build_resources_tree()

        values = []
        for resource in resource_data:
            resource_path = resource.path

            # First, find folders that want to be created but already exist.
            # If so, this is a no-op, so we can skip them.
            if resource.resource_type == ResourceType.FOLDER:
                if any(res.is_relative_to(resource_path) for res in tree):
                    continue

            # Otherwise, create the resource.
            parts = resource_path.parts
            # First part
            first_part = parts[0]
            resource_id = str(uuid.uuid4())
            value = {
                "study_id": self._study_id,
                "id": resource_id,
                "name": first_part,
                "parent_id": None,
                "resource_type": ResourceType.FOLDER if len(parts) > 1 else resource.resource_type,
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
            upsert_multiple(self._db_session, _TABLE, values)
        except IntegrityError as e:
            raise ValueError(f"Could not save user resources {resource_data}") from e

        self._db_session.commit()

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        tree = self._build_resources_tree()
        for resource, data in tree.items():
            if resource.is_relative_to(resource_path):
                relative_path_parts_length = len(resource.relative_to(resource_path).parts)
                id_to_remove = data.ids[-1 - relative_path_parts_length]

                stmt = delete(_TABLE).where((_TABLE.c.study_id == self._study_id) & (_TABLE.c.id == id_to_remove))
                self._db_session.execute(stmt)
                self._db_session.commit()
                return

        raise UserResourcesNotFound(str(resource_path))

    @override
    def get_all_user_resources(self) -> list[UserResourceDataCreation]:
        tree = self._build_resources_tree()
        return [
            UserResourceDataCreation(path=path, resource_type=data.resource_type, blob_id=data.blob_id)
            for path, data in tree.items()
        ]

    def _build_resources_tree(self) -> dict[PurePosixPath, UserResourcesDatabaseData]:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)

        rows = self._db_session.execute(stmt).fetchall()

        # Index by id
        nodes = {row.id: row for row in rows}

        # Determine which nodes are leaves
        parent_ids = {row.parent_id for row in rows if row.parent_id}

        cache: dict[PurePosixPath, tuple[PurePosixPath, UserResourcesDatabaseData]] = {}

        def get_path(node_id: str) -> tuple[PurePosixPath, UserResourcesDatabaseData]:
            """Returns (path, id_chain) for a node."""
            node_id_as_path = PurePosixPath(node_id)
            if node_id_as_path in cache:
                return cache[node_id_as_path]

            node = nodes[node_id]

            if node.parent_id is None:
                data = UserResourcesDatabaseData(ids=[node_id], blob_id=node.blob_id, resource_type=node.resource_type)
                result = (PurePosixPath(node.name), data)
            else:
                parent_path, parent_data = get_path(node.parent_id)
                data = UserResourcesDatabaseData(
                    ids=[*parent_data.ids, node_id], blob_id=node.blob_id, resource_type=node.resource_type
                )
                result = (parent_path.joinpath(node.name), data)

            cache[node_id_as_path] = result
            return result

        return {path: ids for node_id in nodes if node_id not in parent_ids for path, ids in [get_path(node_id)]}
