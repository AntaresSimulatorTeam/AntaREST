# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.favorite.model import FavoriteDTO
from antarest.favorite.service import FavoriteService
from antarest.login.auth import Auth, logger


def create_favorite_routes(favorite_service: FavoriteService, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.favorite], dependencies=[auth.required()])

    @bp.get("/favorite", summary="Listing favorites for current user")
    def list_favorites() -> list[FavoriteDTO]:
        logger.info("Listing favorites for current user")
        return favorite_service.list_favorites()

    @bp.post("/favorite/{uuid}", summary="Create new favorite")
    def add_favorite(uuid: str) -> FavoriteDTO:
        logger.info("Creating new favorite for current user")
        return favorite_service.add_favorite(uuid)

    @bp.delete("/favorite/{uuid}", summary="Delete a favorite")
    def delete_favorite(uuid: str) -> None:
        logger.info("Deleting favorite for current user")
        favorite_service.delete_favorite(uuid)

    return bp
