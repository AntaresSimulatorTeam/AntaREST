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
import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from helpers import with_db_context

from antarest.core.jwt import JWTUser
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.service import FavoriteDirectoryService
from antarest.login.utils import current_user_context
from antarest.study.directory_service import DirectoryService
from antarest.study.model import Directory
from antarest.study.repository import DirectoryRepository


@pytest.fixture
def mock_directory_repo() -> Mock:
    return Mock(spec=DirectoryRepository)


@pytest.fixture
def directory_service(mock_directory_repo):
    return DirectoryService(mock_directory_repo)


@with_db_context
def test_add_favorite_directory(favorite_directory_service: FavoriteDirectoryService, admin_user: JWTUser) -> None:
    directory_1 = Directory(id=str(uuid.uuid4()), name="directory_test_1", parent_id=None)

    directory_2 = Directory(id=str(uuid.uuid4()), name="directory_test_2", parent_id=None)

    db.session.add(directory_1)
    db.session.commit()
    db.session.add(directory_2)
    db.session.commit()

    with current_user_context(admin_user):
        directory_dto_1 = favorite_directory_service.add_favorite(directory_1.id)
        directory_dto_2 = favorite_directory_service.add_favorite(directory_2.id)

        expected_directories = [directory_dto_1, directory_dto_2]
        actual_directories = favorite_directory_service.list_favorites()

        assert actual_directories == expected_directories


@with_db_context
def test_delete_favorite_directory(favorite_directory_service: FavoriteDirectoryService, admin_user: JWTUser) -> None:
    directory_1 = Directory(id=str(uuid.uuid4()), name="directory_test_1", parent_id=None)

    directory_2 = Directory(id=str(uuid.uuid4()), name="directory_test_2", parent_id=None)

    db.session.add(directory_1)
    db.session.commit()
    db.session.add(directory_2)
    db.session.commit()

    with current_user_context(admin_user):
        directory_dto_1 = favorite_directory_service.add_favorite(directory_1.id)
        directory_dto_2 = favorite_directory_service.add_favorite(directory_2.id)
        expected_directories = [directory_dto_1, directory_dto_2]
        actual_directories = favorite_directory_service.list_favorites()
        assert actual_directories == expected_directories

        favorite_directory_service.delete_favorite(directory_dto_1.directory_id)
        assert favorite_directory_service.list_favorites() == [directory_dto_2]

        favorite_directory_service.delete_favorite(directory_dto_2.directory_id)
        assert favorite_directory_service.list_favorites() == []


@with_db_context
def test_add_favorite_directory_failure(
    favorite_directory_service: FavoriteDirectoryService, admin_user: JWTUser
) -> None:
    non_existing_directory_id = "not_existing_directory"

    with current_user_context(admin_user):
        with pytest.raises(HTTPException, match=f"404: Directory with id {non_existing_directory_id} not found"):
            favorite_directory_service.add_favorite(non_existing_directory_id)


@with_db_context
def test_delete_favorite_directory_failure(
    favorite_directory_service: FavoriteDirectoryService, admin_user: JWTUser
) -> None:
    non_existing_directory_id = "not_existing_directory"
    with current_user_context(admin_user):
        with pytest.raises(HTTPException, match=f"404: Directory with id {non_existing_directory_id} not found"):
            favorite_directory_service.delete_favorite(non_existing_directory_id)


@with_db_context
def test_list_favorite_directory_already_existing(
    favorite_directory_service: FavoriteDirectoryService, admin_user: JWTUser
) -> None:
    directory_1 = Directory(id=str(uuid.uuid4()), name="directory_test_1", parent_id=None)

    db.session.add(directory_1)
    db.session.commit()

    with current_user_context(admin_user):
        fav_dto_test = favorite_directory_service.add_favorite(directory_1.id)

        favorite_directory_service.add_favorite(directory_1.id)
        actual_favorite_list = favorite_directory_service.list_favorites()
        assert actual_favorite_list == [fav_dto_test]

        # adding the same directory again should not change the list or the favorite
        favorite_directory_service.add_favorite(directory_1.id)
        actual_favorite_list = favorite_directory_service.list_favorites()
        assert actual_favorite_list == [fav_dto_test]
