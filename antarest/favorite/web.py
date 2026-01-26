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

from antarest.core.config import Config
from antarest.core.utils.web import APITag
from antarest.favorite.model import FavoriteStudyDTO
from antarest.favorite.service import FavoriteStudyService
from antarest.login.auth import Auth, logger


def create_favorite_routes(favorite_service: FavoriteStudyService, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.favorite], dependencies=[auth.required()])

    @bp.get("/favorite_study", summary="Listing favorites for current user")
    def list_favorites() -> list[FavoriteStudyDTO]:
        logger.info("Listing favorites for current user")
        return favorite_service.list_favorites()

    @bp.post("/favorite_study/{uuid}", summary="Create new favorite_study")
    def add_favorite(uuid: str) -> FavoriteStudyDTO:
        logger.info("Creating new favorite_study for current user")
        return favorite_service.add_favorite(uuid)

    @bp.delete("/favorite_study/{uuid}", summary="Delete a favorite_study")
    def delete_favorite(uuid: str) -> None:
        logger.info("Deleting favorite_study for current user")
        favorite_service.delete_favorite(uuid)

    return bp
