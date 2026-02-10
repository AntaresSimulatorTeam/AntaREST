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
import http

from fastapi import HTTPException

from antarest.favorite.model import FavoriteDirectory, FavoriteDirectoryDTO, FavoriteStudy, FavoriteStudyDTO
from antarest.favorite.repository import FavoriteDirectoryRepository, FavoriteStudyRepository
from antarest.login.utils import get_user_impersonator


class FavoriteStudyService:
    def __init__(self, favorite_study_repository: FavoriteStudyRepository):
        self.favorite_repository = favorite_study_repository

    def list_favorites(self) -> list[FavoriteStudyDTO]:
        """
        List all favorites from the current user
        Returns: The list of favorite studies DTOs of the current user in ascending order
        """
        favorites = self.favorite_repository.get_all()
        dto_favorites = [fav.to_dto() for fav in favorites]
        dto_favorites = sorted(dto_favorites, key=lambda fav: fav.study_name)
        return dto_favorites

    def add_favorite(self, study_uuid: str) -> FavoriteStudyDTO:
        """
        Add a favorite to the current user list of favorites
        Args:
            study_uuid: the selected study id
        Returns: the saved FavoriteStudyDTO, made from the user_impersonator and the study id
        """
        study = self.favorite_repository.get(study_uuid)
        if study:
            favorite_study = self.favorite_repository.save(
                FavoriteStudy(user_id=get_user_impersonator(), study_id=study_uuid)
            )
        else:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"Study with id {study_uuid} not found"
            ) from None
        return favorite_study.to_dto()

    def delete_favorite(self, study_uuid: str) -> None:
        """
        Delete a favorite from the current user list of favorites
        Args:
            study_uuid: the selected study id
        """
        study = self.favorite_repository.get(study_uuid)
        if study:
            self.favorite_repository.delete(study_uuid)
        else:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"Study with id {study_uuid} not found"
            ) from None


class FavoriteDirectoryService:
    def __init__(self, favorite_directory_repository: FavoriteDirectoryRepository):
        self.favorite_directory_repository = favorite_directory_repository

    def list_favorites(self) -> list[FavoriteDirectoryDTO]:
        """
        List all favorite directories from the current user
        Returns: The list of favorite directories DTOs of the current user in ascending order
        """
        favorite_directory = self.favorite_directory_repository.get_all()
        dto_favorites = [directory.to_dto() for directory in favorite_directory]
        dto_favorites = sorted(dto_favorites, key=lambda directory: directory.directory_name)
        return dto_favorites

    def add_favorite(self, directory_uuid: str) -> FavoriteDirectoryDTO:
        """
        Add a favorite directory to the current user list of favorites
        Args:
            directory_uuid: the selected directory id
        Returns: the saved FavoriteDirectoryDTO, made from the user_impersonator and the study id
        """
        study = self.favorite_directory_repository.get(directory_uuid)
        if study:
            favorite_directory = self.favorite_directory_repository.save(
                FavoriteDirectory(user_id=get_user_impersonator(), directory_id=directory_uuid)
            )
            return favorite_directory.to_dto()
        else:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"Directory with id {directory_uuid} not found"
            ) from None

    def delete_favorite(self, directory_uuid: str) -> None:
        """
        Delete a favorite directory from the current user list of favorites
        Args:
            directory_uuid: the selected directory id
        """
        study = self.favorite_directory_repository.get(directory_uuid)
        if study:
            self.favorite_directory_repository.delete(directory_uuid)
        else:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"Directory with id {directory_uuid} not found"
            ) from None
