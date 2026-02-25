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

from fastapi import APIRouter

from antarest.core.api_types import SanitizedStr
from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.favorite.model import FavoriteDirectoryDTO, FavoriteStudyDTO
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.login.auth import Auth, logger


def create_favorite_routes(
    favorite_service: FavoriteStudyService, favorite_directory_service: FavoriteDirectoryService, config: Config
) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.favorite], dependencies=[auth.required()])

    @bp.get("/favorites/studies/", summary="Listing favorites for current user")
    def list_favorite_studies() -> list[FavoriteStudyDTO]:
        logger.info("Listing favorites for current user")
        return favorite_service.list_favorites()

    @bp.post("/favorites/studies/{uuid}", summary="Add a study in the list of favorite studies")
    def add_favorite_study(uuid: SanitizedStr) -> FavoriteStudyDTO:
        logger.info("Creating new favorite study for current user")
        return favorite_service.add_favorite(uuid)

    @bp.delete("/favorites/studies/{uuid}", summary="Delete a study from the ")
    def delete_favorite_study(uuid: SanitizedStr) -> None:
        logger.info("Deleting favorite study for current user")
        favorite_service.delete_favorite(uuid)

    @bp.get("/favorites/directories", summary="Listing favorite directories for current user")
    def list_favorite_directories() -> list[FavoriteDirectoryDTO]:
        logger.info("Listing favorite directories for current user")
        return favorite_directory_service.list_favorites()

    @bp.post("/favorites/directories/{uuid}", summary="Add a directory in the list of favorite directories")
    def add_favorite_directory(uuid: SanitizedStr) -> FavoriteDirectoryDTO:
        logger.info("Creating new favorite directory for current user")
        return favorite_directory_service.add_favorite(uuid)

    @bp.delete("/favorites/directories/{uuid}", summary="Delete a directory from the list of favorite directories")
    def delete_favorite_directory(uuid: SanitizedStr) -> None:
        logger.info("Deleting a favorite directory for current user")
        favorite_directory_service.delete_favorite(uuid)

    return bp
