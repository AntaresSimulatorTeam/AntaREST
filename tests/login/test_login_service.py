# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import typing as t
from unittest.mock import patch

import pytest

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.login.model import (
    ADMIN_ID,
    Bot,
    BotCreateDTO,
    BotRoleCreateDTO,
    Group,
    Password,
    Role,
    RoleCreationDTO,
    User,
    UserCreateDTO,
    UserLdap,
)
from antarest.login.service import LoginService
from tests.helpers import with_db_context

# For the unit tests, we will define several fictitious users, groups and roles.

GroupObj = t.TypedDict("GroupObj", {"id": str, "name": str})
UserObj = t.TypedDict("UserObj", {"id": int, "name": str})
RoleObj = t.TypedDict("RoleObj", {"type": RoleType, "group_id": str, "identity_id": int})


_GROUPS: t.List[GroupObj] = [
    {"id": "admin", "name": "X-Men"},
    {"id": "superman", "name": "Superman"},
    {"id": "metropolis", "name": "Metropolis"},
]


_USERS: t.List[UserObj] = [
    # main characters
    {"id": ADMIN_ID, "name": "Professor Xavier"},  # site admin
    {"id": 2, "name": "Clark Kent"},  # admin of "Superman" group
    {"id": 3, "name": "Lois Lane"},  # reader in "Superman" group
    {"id": 4, "name": "Joh Fredersen"},  # "Metropolis" leader
    {"id": 5, "name": "Freder Fredersen"},  # reader in "Metropolis" group
    # secondary characters
    {"id": 50, "name": "Storm"},  # evil man in "X-Men" group
    {"id": 60, "name": "Livewire"},  # evil woman in "Superman" group
    {"id": 70, "name": "Maria"},  # robot in "Metropolis" group
    {"id": 80, "name": "Jane DOE"},  # external user
]

_ROLES: t.List[RoleObj] = [
    {"type": RoleType.ADMIN, "group_id": "admin", "identity_id": ADMIN_ID},
    {"type": RoleType.ADMIN, "group_id": "superman", "identity_id": 2},
    {"type": RoleType.READER, "group_id": "superman", "identity_id": 3},
    {"type": RoleType.ADMIN, "group_id": "metropolis", "identity_id": 4},
    {"type": RoleType.READER, "group_id": "metropolis", "identity_id": 5},
]


def get_jwt_user(user: User, roles: t.Iterable[Role], owner_id: int = 0) -> JWTUser:
    jwt_user = JWTUser(
        id=user.id,
        impersonator=owner_id or user.id,
        type="users",
        groups=[JWTGroup(id=role.group.id, name=role.group.name, role=role.type) for role in roles],
    )
    return jwt_user


def get_request_param(
    user: t.Union[User, UserLdap, Bot],
    role: t.Optional[Role],
    owner_id: int = 0,
) -> RequestParameters:
    if user is None:
        return RequestParameters(user=None)
    roles = (role,) if role else ()
    jwt_user = get_jwt_user(user, roles, owner_id=owner_id)
    return RequestParameters(user=jwt_user)


def get_user_param(login_service: LoginService, user_id: int, group_id: str = "(unknown)") -> RequestParameters:
    user = login_service.users.get(user_id) or login_service.ldap.get(user_id)
    assert user is not None
    role = login_service.roles.get(user_id, group_id)
    return get_request_param(user, role)


def get_bot_param(login_service: LoginService, bot_id: int, group_id: str = "(unknown)") -> RequestParameters:
    bot = login_service.bots.get(bot_id)
    assert bot is not None
    role = login_service.roles.get(bot_id, group_id)
    return get_request_param(bot, role, owner_id=bot.owner)


class TestLoginService:
    """
    Test login service.
    """

    @pytest.fixture(name="populate_db", autouse=True)
    @with_db_context
    def populate_db_fixture(self, login_service: LoginService) -> None:
        for group in _GROUPS:
            login_service.groups.save(Group(**group))
        main_characters = (u for u in _USERS if u["id"] < 10)
        for user in main_characters:
            login_service.users.save(User(**user))
        for role in _ROLES:
            group = t.cast(Group, login_service.groups.get(role["group_id"]))
            user = t.cast(User, login_service.users.get(role["identity_id"]))
            role = Role(**role, group=group, identity=user)
            login_service.roles.save(role)

    @with_db_context
    def test_save_group(self, login_service: LoginService) -> None:
        # site admin can update any group
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.save_group(Group(id="superman", name="Poor Men"), _param)
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Poor Men"

        # Group admin can update his own group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        login_service.save_group(Group(id="superman", name="Man of Steel"), _param)
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Man of Steel"

        # Another user of the same group cannot update the group
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        with pytest.raises(Exception):
            login_service.save_group(Group(id="superman", name="Woman of Steel"), _param)
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Man of Steel"  # not updated

        # Group admin cannot update another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.save_group(Group(id="metropolis", name="Man of Steel"), _param)
        actual = login_service.groups.get("metropolis")
        assert actual is not None
        assert actual.name == "Metropolis"  # not updated

    @with_db_context
    def test_create_user(self, login_service: LoginService) -> None:
        # Site admin can create a user
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.create_user(UserCreateDTO(name="Laurent", password="S3cr3t"), _param)
        actual = login_service.users.get_by_name("Laurent")
        assert actual is not None
        assert actual.name == "Laurent"

        # Group admin cannot create a user
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.create_user(UserCreateDTO(name="Alexandre", password="S3cr3t"), _param)
        actual = login_service.users.get_by_name("Alexandre")
        assert actual is None

    @with_db_context
    def test_save_user(self, login_service: LoginService) -> None:
        # Prepare a new user
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        user = login_service.create_user(UserCreateDTO(name="Laurentius", password="S3cr3t"), _param)

        # Only site admin can update a user
        login_service.save_user(User(id=user.id, name="Lawrence"), _param)
        actual = login_service.users.get(user.id)
        assert actual is not None
        assert actual.name == "Lawrence"

        # Group admin cannot update a user
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.save_user(User(id=user.id, name="Loran"), _param)
            actual = login_service.users.get(user.id)
            assert actual is not None
            assert actual.name == "Lawrence"

        # A user can update himself
        _param = get_user_param(login_service, user_id=user.id)
        login_service.save_user(User(id=user.id, name="Loran"), _param)
        actual = login_service.users.get(user.id)
        assert actual is not None
        assert actual.name == "Loran"

    @with_db_context
    def test_save_bot(self, login_service: LoginService) -> None:
        # Joh Fredersen can create Maria because he is the leader of Metropolis
        _param = get_user_param(login_service, user_id=4, group_id="metropolis")
        login_service.save_bot(BotCreateDTO(name="Maria I", roles=[]), _param)
        actual: t.Sequence[Role] = login_service.bots.get_all_by_owner(4)
        assert len(actual) == 1
        assert actual[0].name == "Maria I"

        # Freder Fredersen can create Maria with the reader role
        _param = get_user_param(login_service, user_id=5, group_id="metropolis")
        login_service.save_bot(
            BotCreateDTO(
                name="Maria II",
                roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.READER.value)],
            ),
            _param,
        )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create Maria with the admin role
        _param = get_user_param(login_service, user_id=5, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="Maria III",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                ),
                _param,
            )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot with an empty name
        _param = get_user_param(login_service, user_id=5, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                ),
                _param,
            )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot that already exists
        _param = get_user_param(login_service, user_id=5, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="Maria II",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                ),
                _param,
            )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot with an invalid group
        _param = get_user_param(login_service, user_id=5, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="Maria III",
                    roles=[BotRoleCreateDTO(group="metropolis2", role=RoleType.ADMIN.value)],
                ),
                _param,
            )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Bot's name cannot be empty
        _param = get_user_param(login_service, user_id=4, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                ),
                _param,
            )

        # Avoid duplicate bots
        _param = get_user_param(login_service, user_id=4, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.save_bot(
                BotCreateDTO(
                    name="Maria I",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                ),
                _param,
            )

    @with_db_context
    def test_save_role(self, login_service: LoginService) -> None:
        # Prepare a new group and a new user
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.groups.save(Group(id="web", name="Spider Web"))
        login_service.users.save(User(id=20, name="Spider-man"))
        login_service.users.save(User(id=21, name="Spider-woman"))

        # The site admin can create a role
        login_service.save_role(
            RoleCreationDTO(type=RoleType.ADMIN, group_id="web", identity_id=20),
            _param,
        )
        actual = login_service.roles.get(20, "web")
        assert actual is not None
        assert actual.type == RoleType.ADMIN

        # The group admin can create a role
        _param = get_user_param(login_service, user_id=20, group_id="web")
        login_service.save_role(
            RoleCreationDTO(type=RoleType.WRITER, group_id="web", identity_id=21),
            _param,
        )
        actual = login_service.roles.get(21, "web")
        assert actual is not None
        assert actual.type == RoleType.WRITER

        # The group admin cannot create a role with an invalid group
        _param = get_user_param(login_service, user_id=20, group_id="web")
        with pytest.raises(Exception):
            login_service.save_role(
                RoleCreationDTO(type=RoleType.WRITER, group_id="web2", identity_id=21),
                _param,
            )
        actual = login_service.roles.get(21, "web")
        assert actual is not None
        assert actual.type == RoleType.WRITER

        # The user cannot create a role
        _param = get_user_param(login_service, user_id=21, group_id="web")
        with pytest.raises(Exception):
            login_service.save_role(
                RoleCreationDTO(type=RoleType.READER, group_id="web", identity_id=20),
                _param,
            )
        actual = login_service.roles.get(20, "web")
        assert actual is not None
        assert actual.type == RoleType.ADMIN

    @with_db_context
    def test_get_group(self, login_service: LoginService) -> None:
        # Site admin can get any group
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_group("superman", _param)
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin can get his own group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_group("superman", _param)
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin cannot get another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_group("metropolis", _param)

        # Lois Lane can get its own group
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        actual = login_service.get_group("superman", _param)
        assert actual is not None
        assert actual.id == "superman"

    @with_db_context
    def test_get_group_info(self, login_service: LoginService) -> None:
        # Site admin can get any group
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_group_info("superman", _param)
        assert actual is not None
        assert actual.name == "Superman"
        assert [obj.model_dump() for obj in actual.users] == [
            {"id": 2, "name": "Clark Kent", "role": RoleType.ADMIN},
            {"id": 3, "name": "Lois Lane", "role": RoleType.READER},
        ]

        # Group admin can get his own group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_group_info("superman", _param)
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin cannot get another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_group_info("metropolis", _param)

        # Lois Lane cannot get its own group
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_group_info("superman", _param)

    @with_db_context
    def test_get_user(self, login_service: LoginService) -> None:
        # Site admin can get any user
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_user(2, _param)
        assert actual is not None
        assert actual.name == "Clark Kent"

        # Group admin can get a user of his own group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_user(3, _param)
        assert actual is not None
        assert actual.name == "Lois Lane"

        # Group admin cannot get a user of another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_user(5, _param)
        assert actual is None

        # Lois Lane can get its own user
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        actual = login_service.get_user(3, _param)
        assert actual is not None
        assert actual.name == "Lois Lane"

        # Create a bot for Lois Lane
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        bot = login_service.save_bot(BotCreateDTO(name="Lois bot", roles=[]), _param)

        # The bot can get its owner
        _param = get_bot_param(login_service, bot_id=bot.id)
        actual = login_service.get_user(3, _param)
        assert actual is not None
        assert actual.name == "Lois Lane"

    @with_db_context
    def test_get_identity(self, login_service: LoginService) -> None:
        # Create the admin user "Storm"
        storm = login_service.users.save(User(id=50, name="Storm"))
        # Create the LDAP user "Jane DOE"
        jane = login_service.users.save(UserLdap(id=60, name="Jane DOE"))
        # Create the bot "Maria"
        maria = login_service.users.save(Bot(id=70, name="Maria", owner=50, is_author=False))

        assert login_service.get_identity(50, include_token=False) == storm
        assert login_service.get_identity(60, include_token=False) == jane
        assert login_service.get_identity(70, include_token=False) is None

        assert login_service.get_identity(50, include_token=True) == storm
        assert login_service.get_identity(60, include_token=True) == jane
        assert login_service.get_identity(70, include_token=True) == maria

    @with_db_context
    def test_get_user_info(self, login_service: LoginService) -> None:
        # Site admin can get any user
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        clark_id = 2
        actual = login_service.get_user_info(clark_id, _param)
        assert actual is not None
        assert actual.model_dump() == {
            "id": clark_id,
            "name": "Clark Kent",
            "roles": [
                {
                    "group_id": "superman",
                    "group_name": "Superman",
                    "identity_id": clark_id,
                    "type": RoleType.ADMIN,
                }
            ],
        }

        # Group admin can get a user of his own group
        _param = get_user_param(login_service, user_id=clark_id, group_id="superman")
        lois_id = 3
        actual = login_service.get_user_info(lois_id, _param)
        assert actual is not None
        assert actual.model_dump() == {
            "id": lois_id,
            "name": "Lois Lane",
            "roles": [
                {
                    "group_id": "superman",
                    "group_name": "Superman",
                    "identity_id": lois_id,
                    "type": RoleType.READER,
                }
            ],
        }

        # Group admin cannot get a user of another group
        _param = get_user_param(login_service, user_id=clark_id, group_id="superman")
        freder_id = 5
        actual = login_service.get_user_info(freder_id, _param)
        assert actual is None

        # Lois Lane can get its own user info
        _param = get_user_param(login_service, user_id=lois_id, group_id="superman")
        actual = login_service.get_user_info(lois_id, _param)
        assert actual is not None
        assert actual.model_dump() == {
            "id": lois_id,
            "name": "Lois Lane",
            "roles": [
                {
                    "group_id": "superman",
                    "group_name": "Superman",
                    "identity_id": lois_id,
                    "type": RoleType.READER,
                }
            ],
        }

        # Create a bot for Lois Lane
        _param = get_user_param(login_service, user_id=lois_id, group_id="superman")
        bot = login_service.save_bot(BotCreateDTO(name="Lois bot", roles=[]), _param)

        # The bot can get its owner
        _param = get_bot_param(login_service, bot_id=bot.id)
        actual = login_service.get_user_info(lois_id, _param)
        assert actual is not None
        assert actual.model_dump() == {
            "id": lois_id,
            "name": "Lois Lane",
            "roles": [
                {
                    "group_id": "superman",
                    "group_name": "Superman",
                    "identity_id": lois_id,
                    "type": RoleType.READER,
                }
            ],
        }

    @with_db_context
    def test_get_bot(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="metropolis")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can get any bot
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_bot(joh_bot.id, _param)
        assert actual is not None
        assert actual.name == "Maria"

        # Joh Fredersen can get its own bot
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        actual = login_service.get_bot(joh_bot.id, _param)
        assert actual is not None
        assert actual.name == "Maria"

        # The bot cannot get itself
        _param = get_bot_param(login_service, bot_id=joh_bot.id)
        with pytest.raises(Exception):
            login_service.get_bot(joh_bot.id, _param)

        # Freder Fredersen cannot get the bot
        freder_id = 5
        _param = get_user_param(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_bot(joh_bot.id, _param)

    @with_db_context
    def test_get_bot_info(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can get any bot
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_bot_info(joh_bot.id, _param)
        assert actual is not None
        assert actual.model_dump() == {"id": 6, "isAuthor": True, "name": "Maria", "roles": []}

        # Joh Fredersen can get its own bot
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        actual = login_service.get_bot_info(joh_bot.id, _param)
        assert actual is not None
        assert actual.model_dump() == {"id": 6, "isAuthor": True, "name": "Maria", "roles": []}

        # The bot cannot get itself
        _param = get_bot_param(login_service, bot_id=joh_bot.id)
        with pytest.raises(Exception):
            login_service.get_bot_info(joh_bot.id, _param)

        # Freder Fredersen cannot get the bot
        freder_id = 5
        _param = get_user_param(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_bot_info(joh_bot.id, _param)

        # Freder Fredersen cannot get the bot
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        with pytest.raises(Exception):
            login_service.get_bot_info(999, _param)

    @with_db_context
    def test_get_all_bots_by_owner(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can get any bot
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_all_bots_by_owner(joh_id, _param)
        expected = [{"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id}]
        assert [obj.to_dto().model_dump() for obj in actual] == expected

        # Freder Fredersen can get its own bot
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        actual = login_service.get_all_bots_by_owner(joh_id, _param)
        expected = [{"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id}]
        assert [obj.to_dto().model_dump() for obj in actual] == expected

        # The bot cannot get itself
        _param = get_bot_param(login_service, bot_id=joh_bot.id)
        with pytest.raises(Exception):
            login_service.get_all_bots_by_owner(joh_id, _param)

        # Freder Fredersen cannot get the bot
        freder_id = 5
        _param = get_user_param(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_all_bots_by_owner(joh_id, _param)

    @with_db_context
    def test_exists_bot(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # Everybody can check the existence of a bot
        assert login_service.exists_bot(joh_id) is False, "not a bot"
        assert login_service.exists_bot(joh_bot.id) is True
        assert login_service.exists_bot(999) is False

    @with_db_context
    def test_authenticate(self, login_service: LoginService) -> None:
        # Update the password of "Lois Lane"
        lois_id = 3
        login_service.users.save(User(id=lois_id, name="Lois Lane", password=Password("S3cr3t")))

        # A known user can log in
        jwt_user = login_service.authenticate(name="Lois Lane", pwd="S3cr3t")
        assert jwt_user is not None
        assert jwt_user.id == lois_id
        assert jwt_user.impersonator == lois_id
        assert jwt_user.type == "users"
        assert jwt_user.groups == [
            JWTGroup(id="superman", name="Superman", role=RoleType.READER),
        ]

        # An unknown user cannot log in
        user = login_service.authenticate(name="unknown", pwd="S3cr3t")
        assert user is None

        # Update the user "Jane DOE" which is an LDAP user
        jane_id = 60
        user_ldap = UserLdap(
            id=jane_id,
            name="Jane DOE",
            external_id="j.doe",
            firstname="Jane",
            lastname="DOE",
        )
        login_service.users.save(user_ldap)

        # Mock the LDAP service
        with patch("antarest.login.ldap.LdapService.login") as mock_login:
            mock_login.return_value = user_ldap
            with patch("antarest.login.ldap.LdapService.login") as mock_get:
                mock_get.return_value = user_ldap
                jwt_user = login_service.authenticate(name="Jane DOE", pwd="S3cr3t")

        assert jwt_user is not None
        assert jwt_user.id == user_ldap.id
        assert jwt_user.impersonator == user_ldap.id
        assert jwt_user.type == "users_ldap"
        assert jwt_user.groups == []

    @with_db_context
    def test_get_jwt(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # Update the user "Jane DOE" which is an LDAP user
        jane_id = 60
        user_ldap = UserLdap(
            id=jane_id,
            name="Jane DOE",
            external_id="j.doe",
            firstname="Jane",
            lastname="DOE",
        )
        login_service.users.save(user_ldap)

        # We can get a JWT for a user, an LDAP user, but not a bot
        lois_id = 3
        jwt_user = login_service.get_jwt(lois_id)
        assert jwt_user is not None
        assert jwt_user.id == lois_id
        assert jwt_user.impersonator == lois_id
        assert jwt_user.type == "users"
        assert jwt_user.groups == [JWTGroup(id="superman", name="Superman", role=RoleType.READER)]

        jwt_user = login_service.get_jwt(user_ldap.id)
        assert jwt_user is not None
        assert jwt_user.id == user_ldap.id
        assert jwt_user.impersonator == user_ldap.id
        assert jwt_user.type == "users_ldap"
        assert jwt_user.groups == []

        jwt_user = login_service.get_jwt(joh_bot.id)
        assert jwt_user is None

    @with_db_context
    def test_get_all_groups(self, login_service: LoginService) -> None:
        # The site admin can get all groups
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_all_groups(_param)
        assert [g.model_dump() for g in actual] == [
            {"id": "admin", "name": "X-Men"},
            {"id": "superman", "name": "Superman"},
            {"id": "metropolis", "name": "Metropolis"},
        ]

        # The group admin can its own groups
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_all_groups(_param)
        assert [g.model_dump() for g in actual] == [{"id": "superman", "name": "Superman"}]

        # The user can get its own groups
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        actual = login_service.get_all_groups(_param)
        assert [g.model_dump() for g in actual] == [{"id": "superman", "name": "Superman"}]

    @with_db_context
    def test_get_all_users(self, login_service: LoginService) -> None:
        # The site admin can get all users
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_all_users(_param)
        assert [u.model_dump() for u in actual] == [
            {"id": 1, "name": "Professor Xavier"},
            {"id": 2, "name": "Clark Kent"},
            {"id": 3, "name": "Lois Lane"},
            {"id": 4, "name": "Joh Fredersen"},
            {"id": 5, "name": "Freder Fredersen"},
        ]

        # The group admin can get its own users, but also the users of the other groups
        # note: I don't know why the group admin can get all users -- Laurent
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_all_users(_param)
        assert [u.model_dump() for u in actual] == [
            {"id": 1, "name": "Professor Xavier"},
            {"id": 2, "name": "Clark Kent"},
            {"id": 3, "name": "Lois Lane"},
            {"id": 4, "name": "Joh Fredersen"},
            {"id": 5, "name": "Freder Fredersen"},
        ]

        # The user can get its own users
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        actual = login_service.get_all_users(_param)
        assert [u.model_dump() for u in actual] == [
            {"id": 2, "name": "Clark Kent"},
            {"id": 3, "name": "Lois Lane"},
        ]

    @with_db_context
    def test_get_all_bots(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="superman")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can get all bots
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_all_bots(_param)
        assert [b.to_dto().model_dump() for b in actual] == [
            {"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id},
        ]

        # The group admin cannot access the list of bots
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_all_bots(_param)

        # The user cannot access the list of bots
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_all_bots(_param)

    @with_db_context
    def test_get_all_roles_in_group(self, login_service: LoginService) -> None:
        # The site admin can get all roles in a given group
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        actual = login_service.get_all_roles_in_group("superman", _param)
        assert [b.to_dto().model_dump() for b in actual] == [
            {
                "group": {"id": "superman", "name": "Superman"},
                "identity": {"id": 2, "name": "Clark Kent"},
                "type": RoleType.ADMIN,
            },
            {
                "group": {"id": "superman", "name": "Superman"},
                "identity": {"id": 3, "name": "Lois Lane"},
                "type": RoleType.READER,
            },
        ]

        # The group admin can get all roles his own group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        actual = login_service.get_all_roles_in_group("superman", _param)
        assert [b.to_dto().model_dump() for b in actual] == [
            {
                "group": {"id": "superman", "name": "Superman"},
                "identity": {"id": 2, "name": "Clark Kent"},
                "type": RoleType.ADMIN,
            },
            {
                "group": {"id": "superman", "name": "Superman"},
                "identity": {"id": 3, "name": "Lois Lane"},
                "type": RoleType.READER,
            },
        ]

        # The user cannot access the list of roles
        _param = get_user_param(login_service, user_id=3, group_id="superman")
        with pytest.raises(Exception):
            login_service.get_all_roles_in_group("superman", _param)

    @with_db_context
    def test_delete_group(self, login_service: LoginService) -> None:
        # Create new groups for Lois Lane (3) and Freder Fredersen (5)
        group1 = login_service.groups.save(Group(id="g1", name="Group I"))
        group2 = login_service.groups.save(Group(id="g2", name="Group II"))
        group3 = login_service.groups.save(Group(id="g3", name="Group III"))

        lois = t.cast(User, login_service.users.get(3))  # group admin
        freder = t.cast(User, login_service.users.get(5))  # user

        login_service.roles.save(Role(type=RoleType.ADMIN, group=group1, identity=lois))
        login_service.roles.save(Role(type=RoleType.READER, group=group1, identity=freder))
        login_service.roles.save(Role(type=RoleType.ADMIN, group=group2, identity=lois))
        login_service.roles.save(Role(type=RoleType.WRITER, group=group2, identity=freder))
        login_service.roles.save(Role(type=RoleType.ADMIN, group=group3, identity=lois))
        login_service.roles.save(Role(type=RoleType.RUNNER, group=group3, identity=freder))

        # The site admin can delete any group
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.delete_group("g1", _param)
        assert login_service.groups.get(group1.id) is None

        # The group admin can delete his own group
        _param = get_user_param(login_service, user_id=3, group_id="g2")
        login_service.delete_group("g2", _param)
        assert login_service.groups.get(group2.id) is None

        # The user cannot delete a group
        _param = get_user_param(login_service, user_id=5, group_id="g3")
        with pytest.raises(Exception):
            login_service.delete_group("g3", _param)
        assert login_service.groups.get(group3.id) is not None

    @with_db_context
    def test_delete_user(self, login_service: LoginService) -> None:
        # Create Joh's bot
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="metropolis")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can delete Fredersen (5)
        freder_id = 5
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.delete_user(freder_id, _param)
        assert login_service.users.get(freder_id) is None

        # The group admin Joh can delete himself (4)
        _param = get_user_param(login_service, user_id=joh_id, group_id="metropolis")
        login_service.delete_user(joh_id, _param)
        assert login_service.users.get(joh_id) is None
        assert login_service.bots.get(joh_bot.id) is None

        # Lois Lane cannot delete Clark Kent (2)
        lois_id = 3
        clark_id = 2
        _param = get_user_param(login_service, user_id=lois_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.delete_user(clark_id, _param)
        assert login_service.users.get(clark_id) is not None

        # Clark Kent cannot delete Lois Lane (3)
        _param = get_user_param(login_service, user_id=clark_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.delete_user(lois_id, _param)
        assert login_service.users.get(lois_id) is not None

    @with_db_context
    def test_delete_bot(self, login_service: LoginService) -> None:
        # Create Joh's bot
        joh_id = 4
        _param = get_user_param(login_service, user_id=joh_id, group_id="metropolis")
        joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]), _param)

        # The site admin can delete the bot
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.delete_bot(joh_bot.id, _param)
        assert login_service.bots.get(joh_bot.id) is None

        # Create Lois's bot
        lois_id = 3
        _param = get_user_param(login_service, user_id=lois_id, group_id="superman")
        lois_bot = login_service.save_bot(BotCreateDTO(name="Lois bot", roles=[]), _param)

        # The group admin cannot delete the bot
        clark_id = 2
        _param = get_user_param(login_service, user_id=clark_id, group_id="superman")
        with pytest.raises(Exception):
            login_service.delete_bot(lois_bot.id, _param)
        assert login_service.bots.get(lois_bot.id) is not None

        # Create Freder's bot
        freder_id = 5
        _param = get_user_param(login_service, user_id=freder_id, group_id="metropolis")
        freder_bot = login_service.save_bot(BotCreateDTO(name="Freder bot", roles=[]), _param)

        # Freder can delete his own bot
        _param = get_user_param(login_service, user_id=freder_id, group_id="metropolis")
        login_service.delete_bot(freder_bot.id, _param)
        assert login_service.bots.get(freder_bot.id) is None

        # Freder cannot delete Lois's bot
        _param = get_user_param(login_service, user_id=freder_id, group_id="metropolis")
        with pytest.raises(Exception):
            login_service.delete_bot(lois_bot.id, _param)
        assert login_service.bots.get(lois_bot.id) is not None

    @with_db_context
    def test_delete_role(self, login_service: LoginService) -> None:
        # Create a new group
        group = login_service.groups.save(Group(id="g1", name="Group I"))

        # Create a new user
        user = login_service.users.save(User(id=10, name="User 1"))

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The site admin can delete any role
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.delete_role(role.identity.id, role.group.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin can delete a role of his own group
        _param = get_user_param(login_service, user_id=user.id, group_id="g1")
        login_service.delete_role(role.identity.id, role.group.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin cannot delete a role of another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.delete_role(role.identity.id, "g1", _param)
        assert login_service.roles.get(role.identity.id, "g1") is not None

        # The user cannot delete a role
        _param = get_user_param(login_service, user_id=1, group_id="g1")
        with pytest.raises(Exception):
            login_service.delete_role(role.identity.id, role.group.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is not None

    @with_db_context
    def test_delete_all_roles_from_user(self, login_service: LoginService) -> None:
        # Create a new group
        group = login_service.groups.save(Group(id="g1", name="Group I"))

        # Create a new user
        user = login_service.users.save(User(id=10, name="User 1"))

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The site admin can delete any role
        _param = get_user_param(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.delete_all_roles_from_user(user.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin can delete a role of his own group
        _param = get_user_param(login_service, user_id=user.id, group_id="g1")
        login_service.delete_all_roles_from_user(user.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin cannot delete a role of another group
        _param = get_user_param(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception):
            login_service.delete_all_roles_from_user(user.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is not None

        # The user cannot delete a role
        _param = get_user_param(login_service, user_id=1, group_id="g1")
        with pytest.raises(Exception):
            login_service.delete_all_roles_from_user(user.id, _param)
        assert login_service.roles.get(role.identity.id, role.group.id) is not None
