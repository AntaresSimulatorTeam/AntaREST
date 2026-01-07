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

from antarest.favorite.model import Favorite, FavoriteDTO
from antarest.favorite.repository import FavoriteRepository
from antarest.login.utils import get_user_id


class FavoriteService:
    def __init__(self, favorite_repository: FavoriteRepository):
        self.favorite_repository = favorite_repository

    def list_favorites(self) -> list[FavoriteDTO]:
        favorites = self.favorite_repository.get_all()
        dto_favorites = [fav.to_dto() for fav in favorites]
        return dto_favorites

    def add_favorite(self, study_uuid: str) -> FavoriteDTO:
        favorite = self.favorite_repository.save(Favorite(user_id=get_user_id(), study_id=study_uuid))
        return favorite.to_dto()

    def delete_favorite(self, study_uuid: str) -> None:
        self.favorite_repository.delete(get_user_id(), study_uuid)
