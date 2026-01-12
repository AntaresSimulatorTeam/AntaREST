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

import logging
from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.directory_service import DirectoryService
from antarest.study.model import DirectoryCreation, DirectoryMetadata, DirectoryUpdate

logger = logging.getLogger(__name__)


def create_directory_routes(
    directory_service: DirectoryService,
    config: Config,
) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.directory_management], dependencies=[auth.required()])

    @bp.get(
        "/directories",
        summary="List directories",
    )
    def list_directories() -> List[DirectoryMetadata]:
        logger.info("Listing directories for current user")
        return directory_service.list_directories()

    @bp.post(
        "/directories",
        status_code=HTTPStatus.CREATED,
        summary="Create a new directory",
    )
    def create_directory(data: DirectoryCreation) -> DirectoryMetadata:
        logger.info(f"Creating directory '{data.name}'")
        return directory_service.create_directory(data)

    @bp.patch(
        "/directories/{directory_id}",
        summary="Update directory",
    )
    def update_directory(directory_id: str, data: DirectoryUpdate) -> DirectoryMetadata:
        """
        Update directory name or parent.
        """
        logger.info(f"Updating directory {directory_id}")
        return directory_service.update_directory(directory_id, data)

    @bp.delete(
        "/directories/{directory_id}",
        status_code=HTTPStatus.NO_CONTENT,
        summary="Delete directory",
    )
    def delete_directory(directory_id: str) -> None:
        """
        Delete a directory only if it and all its subdirectories contain no studies.
        """
        logger.info(f"Deleting directory {directory_id}")
        directory_service.delete_directory(directory_id)

    return bp
