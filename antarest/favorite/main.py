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
from typing import Optional

from antarest.core.application import AppBuildContext
from antarest.core.config import Config
from antarest.favorite.repository import FavoriteRepository
from antarest.favorite.service import FavoriteService
from antarest.favorite.web import create_favorite_routes


def build_favorite_service(
    config: Config, app_ctxt: Optional[AppBuildContext] = None, service: Optional[FavoriteService] = None
) -> FavoriteService:
    if service is None:
        favorite_repository = FavoriteRepository()
        service = FavoriteService(favorite_repository=favorite_repository)

    if app_ctxt:
        app_ctxt.api_root.include_router(create_favorite_routes(service, config=config))

    return service
