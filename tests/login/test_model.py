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
from pydantic import ValidationError
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker

from antarest.login.model import (
    ADMIN_ID,
    ADMIN_NAME,
    GROUP_ID,
    GROUP_NAME,
    Group,
    Password,
    Role,
    User,
    UserCreateDTO,
    init_admin_user,
)
from antarest.service_creator import SESSION_ARGS

TEST_ADMIN_PASS_WORD = "test"


def test_password() -> None:
    assert Password("pwd").check("pwd")


class TestPasswordValidation:
    VALID_PASSWORD = "Abcdef1!"

    def test_valid_password_is_accepted(self) -> None:
        dto = UserCreateDTO(name="alice", password=self.VALID_PASSWORD)
        assert dto.password == self.VALID_PASSWORD

    @pytest.mark.parametrize(
        "password, expected_message",
        [
            ("Ab1!xyz", "between 8 and 50 characters"),
            ("A" + "b1!" + "x" * 48, "between 8 and 50 characters"),
            ("ABCDEF1!", "lowercase letter"),
            ("abcdef1!", "uppercase letter"),
            ("Abcdefg!", "digit"),
            ("Abcdefg1", "special character"),
        ],
    )
    def test_invalid_password_is_rejected(self, password: str, expected_message: str) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UserCreateDTO(name="alice", password=password)
        assert expected_message in str(exc_info.value)

    def test_password_exceeding_bcrypt_byte_limit_is_rejected(self) -> None:
        password = "Aa1!" + "🦀" * 20
        assert len(password) <= 50
        assert len(password.encode("utf-8")) > 72
        with pytest.raises(ValidationError) as exc_info:
            UserCreateDTO(name="alice", password=password)
        assert "72 bytes" in str(exc_info.value)


class TestInitAdminUser:
    def test_init_admin_user_nominal(self, db_engine: Engine) -> None:
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            user = session.get(User, ADMIN_ID)
            assert user is not None
            assert user.id == ADMIN_ID
            assert user.name == ADMIN_NAME
            assert user.password.check(TEST_ADMIN_PASS_WORD)
            group = session.get(Group, GROUP_ID)
            assert group is not None
            assert group.id == GROUP_ID
            assert group.name == GROUP_NAME
            role = session.get(Role, (ADMIN_ID, GROUP_ID))
            assert role is not None
            assert role.identity is user
            assert role.group is group

    def test_init_admin_user_redundancy_check(self, db_engine: Engine) -> None:
        # run first time
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
        # run second time
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)

    def test_init_admin_user_existing_group(self, db_engine: Engine) -> None:
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            group = Group(id=GROUP_ID, name=GROUP_NAME)
            session.add(group)
            session.commit()
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)

    def test_init_admin_user_existing_user(self, db_engine: Engine) -> None:
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            user = User(id=ADMIN_ID, name=ADMIN_NAME, password=Password(TEST_ADMIN_PASS_WORD))
            session.add(user)
            session.commit()
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
