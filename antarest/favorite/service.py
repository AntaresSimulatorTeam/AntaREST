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

from antarest.favorite.model import FavoriteStudy, FavoriteStudyDTO
from antarest.favorite.repository import FavoriteRepository
from antarest.login.utils import get_user_impersonator


class FavoriteService:
    def __init__(self, favorite_repository: FavoriteRepository):
        self.favorite_repository = favorite_repository

    def list_favorites(self) -> list[FavoriteStudyDTO]:
        favorites = self.favorite_repository.get_all()
        dto_favorites = [fav.to_dto() for fav in favorites]
        dto_favorites = sorted(dto_favorites, key=lambda fav: fav.study_name)
        return dto_favorites

    def add_favorite(self, study_uuid: str) -> FavoriteStudyDTO:
        favorite_study = self.favorite_repository.save(
            FavoriteStudy(user_id=get_user_impersonator(), study_id=study_uuid)
        )
        return favorite_study.to_dto()

    def delete_favorite(self, study_uuid: str) -> None:
        self.favorite_repository.delete(study_uuid)
