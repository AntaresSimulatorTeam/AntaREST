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

from antarest.blobstore.service import IBlobService
from antarest.core.exceptions import UserResourceIsAFolder, UserResourceNotFound
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

    def __init__(self, study_id: str, db_session: Session, blob_service: IBlobService) -> None:
        """
        Initialize DatabaseUserResourcesDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session
        self._blob_service = blob_service

    @override
    def save_user_resources(self, resource_data: list[UserResourceDataCreation]) -> None:
        tree = self._build_resources_tree()

        values = []
        for resource in resource_data:
            resource_path = resource.path

            # Raise an error if we try to create 2 resources with different type at the same path.
            # This mimics the behavior of the filesystem.
            if resource_path in tree:
                if resource.resource_type != tree[resource_path].resource_type:
                    raise ValueError(f"Cannot create 2 resources of different type at the same path '{resource_path}'")

            # Skip folders that already exist.
            if resource.resource_type == ResourceType.FOLDER and any(res.is_relative_to(resource_path) for res in tree):
                continue

            # Find parent IDs if the resource is relative to an existing one.
            parent_ids = []
            for res, data in tree.items():
                if resource_path.is_relative_to(res) and res != resource_path:
                    parent_ids = data.ids
                    break

            # Build the resource tree.
            parent_id = parent_ids[-1] if parent_ids else None
            ids = []

            # Skip parts covered by parent IDs.
            start_index = len(parent_ids)
            for i, part in enumerate(parts := resource_path.parts[start_index:], start=start_index):
                resource_id = str(uuid.uuid4())
                ids.append(resource_id)

                is_last_part = i == len(parts) - 1

                value = {
                    "study_id": self._study_id,
                    "id": resource_id,
                    "name": part,
                    "parent_id": parent_id,
                    "resource_type": ResourceType.FOLDER if not is_last_part else resource.resource_type,
                    "blob_id": None if not is_last_part else resource.blob_id,
                }

                # Handle resource replacement for files.
                if is_last_part and resource.resource_type == ResourceType.FILE:
                    existing = tree.get(resource_path)
                    if existing is not None:
                        value["id"] = existing.ids[-1]

                values.append(value)
                parent_id = resource_id

            # Update the tree with the new resource to perform checks on the next iteration
            tree[resource_path] = UserResourcesDatabaseData(
                ids=ids, blob_id=resource.blob_id, resource_type=resource.resource_type
            )

        if not values:
            return

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

        raise UserResourceNotFound(str(resource_path))

    @override
    def get_all_user_resources(self) -> list[UserResourceDataCreation]:
        tree = self._build_resources_tree()
        return [
            UserResourceDataCreation(path=path, resource_type=data.resource_type, blob_id=data.blob_id)
            for path, data in tree.items()
        ]

    @override
    def get_user_resource(self, resource_path: PurePosixPath) -> bytes:
        tree = self._build_resources_tree()

        if resource_path not in tree:
            raise UserResourceNotFound(resource_path.as_posix())

        data = tree[resource_path]
        if data.resource_type == ResourceType.FOLDER:
            raise UserResourceIsAFolder(resource_path.as_posix())

        assert data.blob_id is not None
        return self._blob_service.get(data.blob_id)

    def _build_resources_tree(self) -> dict[PurePosixPath, UserResourcesDatabaseData]:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)

        rows = self._db_session.execute(stmt).fetchall()

        # Index by id
        nodes = {row.id: row for row in rows}

        # Determine which nodes are leaves
        parent_ids = {row.parent_id for row in rows if row.parent_id}

        cache: dict[PurePosixPath, tuple[PurePosixPath, UserResourcesDatabaseData]] = {}

        def get_path_and_data(node_id: str) -> tuple[PurePosixPath, UserResourcesDatabaseData]:
            node_id_as_path = PurePosixPath(node_id)
            if node_id_as_path in cache:
                return cache[node_id_as_path]

            node = nodes[node_id]

            if node.parent_id is None:
                data = UserResourcesDatabaseData(ids=[node_id], blob_id=node.blob_id, resource_type=node.resource_type)
                result = (PurePosixPath(node.name), data)
            else:
                parent_path, parent_data = get_path_and_data(node.parent_id)
                data = UserResourcesDatabaseData(
                    ids=[*parent_data.ids, node_id], blob_id=node.blob_id, resource_type=node.resource_type
                )
                result = (parent_path.joinpath(node.name), data)

            cache[node_id_as_path] = result
            return result

        return {
            path: data for node_id in nodes if node_id not in parent_ids for path, data in [get_path_and_data(node_id)]
        }
