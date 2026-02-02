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

from antarest.favorite.model import FavoriteDirectory, FavoriteDirectoryDTO, FavoriteStudy, FavoriteStudyDTO
from antarest.favorite.repository import FavoriteDirectoryRepository, FavoriteStudyRepository
from antarest.login.utils import get_user_impersonator


class FavoriteStudyService:
    def __init__(self, favorite_study_repository: FavoriteStudyRepository):
        self.favorite_repository = favorite_study_repository

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


class FavoriteDirectoryService:
    def __init__(self, favorite_directory_repository: FavoriteDirectoryRepository):
        self.favorite_directory_repository = favorite_directory_repository

    def list_favorites(self) -> list[FavoriteDirectoryDTO]:
        favorite_directory = self.favorite_directory_repository.get_all()
        dto_favorites = [fav.to_dto() for fav in favorite_directory]
        return dto_favorites

    def add_favorite(self, directory_uuid: str) -> FavoriteDirectoryDTO:
        favorite_directory = self.favorite_directory_repository.save(
            FavoriteDirectory(user_id=get_user_impersonator(), directory_id=directory_uuid)
        )
        return favorite_directory.to_dto()

    def delete_favorite(self, directory_uuid: str) -> None:
        self.favorite_directory_repository.delete(get_user_impersonator(), directory_uuid)
