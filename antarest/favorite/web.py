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

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from antarest.core.api_types import UuidStr
from antarest.core.utils.web import APITag
from antarest.dependencies import FavoriteDirectoryServiceDep, FavoriteStudyServiceDep, auth_required
from antarest.favorite.model import FavoriteDirectoryDTO, FavoriteStudyDTO

logger = logging.getLogger(__name__)


def create_favorite_routes() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.favorite], dependencies=[Depends(auth_required)], route_class=DishkaRoute)

    @bp.get("/favorites/studies/", summary="Listing favorites for current user")
    def list_favorite_studies(
        favorite_service: FavoriteStudyServiceDep,
    ) -> list[FavoriteStudyDTO]:
        logger.info("Listing favorites for current user")
        return favorite_service.list_favorites()

    @bp.post("/favorites/studies/{uuid}", summary="Add a study in the list of favorite studies")
    def add_favorite_study(favorite_service: FavoriteStudyServiceDep, uuid: UuidStr) -> FavoriteStudyDTO:
        logger.info(f"Adding study {uuid} as a favorite.")
        return favorite_service.add_favorite(uuid)

    @bp.delete("/favorites/studies/{uuid}", summary="Delete a study from the ")
    def delete_favorite_study(favorite_service: FavoriteStudyServiceDep, uuid: UuidStr) -> None:
        logger.info(f"Deleting study {uuid} from favorites.")
        favorite_service.delete_favorite(uuid)

    @bp.get("/favorites/directories", summary="Listing favorite directories for current user")
    def list_favorite_directories(
        favorite_directory_service: FavoriteDirectoryServiceDep,
    ) -> list[FavoriteDirectoryDTO]:
        logger.info("Listing favorite directories for current user")
        return favorite_directory_service.list_favorites()

    @bp.post("/favorites/directories/{uuid}", summary="Add a directory in the list of favorite directories")
    def add_favorite_directory(
        favorite_directory_service: FavoriteDirectoryServiceDep, uuid: UuidStr
    ) -> FavoriteDirectoryDTO:
        logger.info(f"Adding directory {uuid} as a favorite.")
        return favorite_directory_service.add_favorite(uuid)

    @bp.delete("/favorites/directories/{uuid}", summary="Delete a directory from the list of favorite directories")
    def delete_favorite_directory(favorite_directory_service: FavoriteDirectoryServiceDep, uuid: UuidStr) -> None:
        logger.info(f"Deleting directory {uuid} from favorites.")
        favorite_directory_service.delete_favorite(uuid)

    return bp
