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
    init_admin_user,
)
from antarest.service_creator import SESSION_ARGS

TEST_ADMIN_PASS_WORD = "test"


def test_password():
    assert Password("pwd").check("pwd")


class TestInitAdminUser:
    def test_init_admin_user_nominal(self, db_engine: Engine):
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            user = session.query(User).get(ADMIN_ID)
            assert user is not None
            assert user.id == ADMIN_ID
            assert user.name == ADMIN_NAME
            assert user.password.check(TEST_ADMIN_PASS_WORD)
            group = session.query(Group).get(GROUP_ID)
            assert group is not None
            assert group.id == GROUP_ID
            assert group.name == GROUP_NAME
            role = session.query(Role).get((ADMIN_ID, GROUP_ID))
            assert role is not None
            assert role.identity is user
            assert role.group is group

    def test_init_admin_user_redundancy_check(self, db_engine: Engine):
        # run first time
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
        # run second time
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)

    def test_init_admin_user_existing_group(self, db_engine: Engine):
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            group = Group(id=GROUP_ID, name=GROUP_NAME)
            session.add(group)
            session.commit()
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)

    def test_init_admin_user_existing_user(self, db_engine: Engine):
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            user = User(id=ADMIN_ID, name=ADMIN_NAME, password=Password(TEST_ADMIN_PASS_WORD))
            session.add(user)
            session.commit()
        init_admin_user(db_engine, SESSION_ARGS, admin_password=TEST_ADMIN_PASS_WORD)
