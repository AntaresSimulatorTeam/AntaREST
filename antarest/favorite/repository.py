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

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.orm import Session, joinedload

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.model import FavoriteDirectory, FavoriteExternalDirectory, FavoriteStudy
from antarest.login.utils import get_user_impersonator
from antarest.study.model import Directory, Study


class FavoriteStudyRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def save(self, favorite_study: FavoriteStudy) -> FavoriteStudy:
        """
        Save a favorite study into the favorite database
        Args:
            favorite_study: the favorite study to save
        Returns:
            The saved favorite study
        """
        session = self.session
        fav = session.merge(favorite_study)
        session.add(fav)
        session.commit()
        return fav

    def get_all(self) -> list[FavoriteStudy]:
        """
        List of all the favorite studies belonging to the current user
        Returns: The list of all the favorite studies belonging to the current user
        """
        stmt = (
            select(FavoriteStudy)
            .options(joinedload(FavoriteStudy.study))
            .where((Study.id == FavoriteStudy.study_id) & (FavoriteStudy.user_id == get_user_impersonator()))
        )
        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def get(self, study_id: str) -> Study | None:
        stmt = select(Study).where(Study.id == study_id)
        result = self.session.execute(stmt)

        return result.unique().scalar()

    def delete(self, study_id: str) -> None:
        """
        Delete a favorite study from the current user list / database
        Args:
            study_id: the selected study id to remove from the favourites
        """
        session = self.session
        stmt = (
            delete(FavoriteStudy)
            .where(FavoriteStudy.user_id == get_user_impersonator())
            .where(FavoriteStudy.study_id == study_id)
        )
        session.execute(stmt)
        session.commit()


class FavoriteDirectoryRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def get_all(self) -> list[FavoriteDirectory]:
        """
        List all the favorite directories belonging to the current user
        Returns: The list of all the favorite directories belonging to the current user
        """
        stmt = (
            select(FavoriteDirectory)
            .options(joinedload(FavoriteDirectory.directory))
            .where(
                (Directory.id == FavoriteDirectory.directory_id)
                & (FavoriteDirectory.user_id == get_user_impersonator())
            )
        )
        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def get(self, directory_uuid: str) -> Directory | None:
        stmt = select(Directory).where(Directory.id == directory_uuid)
        result = self.session.execute(stmt)

        return result.unique().scalar()

    def delete(self, directory_id: str) -> None:
        """
        Delete a directory from the current user list / database
        Args:
            directory_id: the selected directory id to remove from the favorites
        """
        session = self.session
        stmt = (
            delete(FavoriteDirectory)
            .where(FavoriteDirectory.user_id == get_user_impersonator())
            .where(FavoriteDirectory.directory_id == directory_id)
        )
        session.execute(stmt)
        session.commit()

    def save(self, directory: FavoriteDirectory) -> FavoriteDirectory:
        """
        Save a favorite directory into the current user list / database
        Args:
            directory: the favorite directory to save
        Returns: the saved favorite directory
        """
        session = self.session
        direct = session.merge(directory)
        session.add(direct)
        session.commit()
        return direct


class FavoriteExternalDirectoryRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def save(self, favorite_external_directory: FavoriteExternalDirectory) -> FavoriteExternalDirectory:
        session = self.session
        fav = session.merge(favorite_external_directory)
        session.add(fav)
        session.commit()
        return fav

    def get_all(self) -> list[FavoriteExternalDirectory]:
        stmt = select(FavoriteExternalDirectory).where(FavoriteExternalDirectory.user_id == get_user_impersonator())
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def delete(self, workspace: str, path: str) -> bool:
        session = self.session
        stmt = (
            delete(FavoriteExternalDirectory)
            .where(FavoriteExternalDirectory.user_id == get_user_impersonator())
            .where(FavoriteExternalDirectory.workspace == workspace)
            .where(FavoriteExternalDirectory.path == path)
        )
        result = session.execute(stmt)
        assert isinstance(result, CursorResult)
        session.commit()
        return result.rowcount > 0
