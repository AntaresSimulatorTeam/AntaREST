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

import pytest
from fastapi import HTTPException

from antarest.core.jwt import JWTUser
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.model import FavoriteStudyDTO
from antarest.favorite.service import FavoriteStudyService
from antarest.login.utils import current_user_context
from tests.helpers import create_study, with_db_context


@with_db_context
def test_add_favorite_study(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    study_1 = create_study(name="study_A")
    study_2 = create_study(name="study_B")

    db.session.add(study_1)
    db.session.commit()
    db.session.add(study_2)
    db.session.commit()

    with current_user_context(admin_user):
        favorite_service.add_favorite(study_1.id)
        favorite_service.add_favorite(study_2.id)
        actual_favorite_list = favorite_service.list_favorites()

    expected_favorite_list = [
        FavoriteStudyDTO(study_id=study_1.id, study_name="study_A"),
        FavoriteStudyDTO(study_id=study_2.id, study_name="study_B"),
    ]
    assert actual_favorite_list == expected_favorite_list


@with_db_context
def test_delete_favorite_study(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    study_1 = create_study("study_A")
    study_2 = create_study("study_B")

    db.session.add(study_1)
    db.session.commit()
    db.session.add(study_2)
    db.session.commit()

    with current_user_context(admin_user):
        favorite_dto_1 = favorite_service.add_favorite(study_1.id)
        favorite_dto_2 = favorite_service.add_favorite(study_2.id)
        actual_favorite_list = favorite_service.list_favorites()
        expected_favorite_list = [favorite_dto_1, favorite_dto_2]

        assert actual_favorite_list == expected_favorite_list
        favorite_service.delete_favorite(favorite_dto_1.study_id)
        favorite_service.delete_favorite(favorite_dto_2.study_id)

        expected_favorite_list = []
        actual_favorite_list = favorite_service.list_favorites()
        assert actual_favorite_list == expected_favorite_list


@with_db_context
def test_delete_favorite_study_failure_not_existing(
    favorite_service: FavoriteStudyService, admin_user: JWTUser
) -> None:
    non_existing_study_id = "not_existing_study"

    with current_user_context(admin_user):
        with pytest.raises(
            HTTPException,
            match=f"404: Study with id {non_existing_study_id} not found",
        ):
            favorite_service.delete_favorite(non_existing_study_id)


@with_db_context
def test_add_favorite_study_failure_not_existing(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    non_existing_study_id = "not_existing_study"

    with current_user_context(admin_user):
        with pytest.raises(
            HTTPException,
            match=f"404: Study with id {non_existing_study_id} not found",
        ):
            favorite_service.add_favorite(non_existing_study_id)


@with_db_context
def test_add_favorite_study_already_existing(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    study_1 = create_study("study_A", "study_A")

    db.session.add(study_1)
    db.session.commit()

    with current_user_context(admin_user):
        favorite_service.add_favorite(study_1.id)
        test_fav_dto = FavoriteStudyDTO(study_id=study_1.id, study_name="study_A")

        actual_favorite_list = favorite_service.list_favorites()

        assert actual_favorite_list == [test_fav_dto]

        # checking that the favorite is not added twice and remains the same
        favorite_service.add_favorite(study_1.id)
        actual_favorite_list = favorite_service.list_favorites()

        assert actual_favorite_list == [test_fav_dto]
