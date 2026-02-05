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
from sqlalchemy.orm import Session

from antarest.core.roles import RoleType
from antarest.login.model import Bot, Group, Password, Role, User, UserLdap
from antarest.login.repository import BotRepository, GroupRepository, RoleRepository, UserLdapRepository, UserRepository


def test_users(db_session: Session) -> None:
    with db_session:
        repo = UserRepository(session=db_session)
        a = User(
            name="a",
            password=Password("a"),
        )
        b = User(name="b", password=Password("b"))

        a = repo.save(a)
        b = repo.save(b)
        assert b.id
        c = repo.get(a.id)
        assert a == c
        assert a.password.check("a")
        assert b == repo.get_by_name("b")

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_users_ldap(db_session: Session) -> None:
    repo = UserLdapRepository(session=db_session)
    with repo.session:
        a = UserLdap(name="a", external_id="b")

        a = repo.save(a)
        assert a.id

        assert repo.get_by_external_id("b") == a

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_bots(db_session: Session) -> None:
    repo = BotRepository(session=db_session)
    with repo.session:
        a = Bot(name="a", owner=1)
        a = repo.save(a)
        assert a.id
        assert a == repo.get(a.id)
        assert [a] == repo.get_all_by_owner(1)
        assert a == repo.get_by_name_and_owner(owner=1, name="a")
        assert not repo.get_by_name_and_owner(owner=1, name="wrong_name")
        assert not repo.get_by_name_and_owner(owner=9, name="a")

        with pytest.raises(ValueError):
            repo.save(a)

        assert repo.exists(a.id)

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_groups(db_session: Session) -> None:
    repo = GroupRepository(session=db_session)
    with repo.session:
        a = Group(name="a")

        a = repo.save(a)
        assert a.id
        assert a == repo.get(a.id)

        b = repo.get_by_name(a.name)
        assert b == a

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_roles(db_session: Session) -> None:
    repo = RoleRepository(session=db_session)
    with repo.session:
        a = Role(type=RoleType.ADMIN, identity=User(id=0), group=Group(id="group"))

        a = repo.save(a)
        assert a == repo.get(user=0, group="group")
        assert [a] == repo.get_all_by_user(0)
        assert [a] == repo.get_all_by_group(group="group")

        repo.delete(user=0, group="group")
        assert repo.get(user=0, group="group") is None
