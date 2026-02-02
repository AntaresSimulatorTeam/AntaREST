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
from antarest.core.jwt import JWTUser
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.favorite.service import FavoriteStudyService
from antarest.login.utils import current_user_context
from tests.helpers import create_study, with_db_context


@with_db_context
def test_add_favorite(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    study_1 = create_study(name="study_A")
    study_2 = create_study(name="study_B")

    db.session.add(study_1)
    db.session.add(study_2)

    with current_user_context(admin_user):
        favorite_dto_1 = favorite_service.add_favorite(study_1.id)
        favorite_dto_2 = favorite_service.add_favorite(study_2.id)
        actual_favorite_list = favorite_service.list_favorites()

    expected_favorite_list = [favorite_dto_1, favorite_dto_2]
    assert actual_favorite_list == expected_favorite_list


@with_db_context
def test_delete_favorite(favorite_service: FavoriteStudyService, admin_user: JWTUser) -> None:
    study_1 = create_study("study_A")
    study_2 = create_study("study_B")

    db.session.add(study_1)
    db.session.add(study_2)

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
