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

import typing as t
from unittest.mock import patch

import pytest
from db_statement_recorder import DBStatementRecorder
from sqlalchemy.orm import Session

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import UserHasNotPermissionError
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
from antarest.login.service import GroupNotFoundError, LoginService
from antarest.login.utils import current_user_context
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


def get_user(login_service: LoginService, user_id: int, group_id: str = "(unknown)") -> JWTUser:
    user = login_service.users.get(user_id) or login_service.ldap.get(user_id)
    assert user is not None
    role = login_service.roles.get(user_id, group_id)
    roles = [role] if role is not None else []
    return JWTUser(
        id=user.id,
        impersonator=user.id,
        type="users",
        groups=[JWTGroup(id=role.group.id, name=role.group.name, role=role.type) for role in roles],
    )


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
        user = get_user(login_service, ADMIN_ID, group_id="admin")
        with current_user_context(user):
            login_service.save_group(Group(id="superman", name="Poor Men"))
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Poor Men"

        # Group admin can update his own group
        user = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(user):
            login_service.save_group(Group(id="superman", name="Man of Steel"))
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Man of Steel"

        # Another user of the same group cannot update the group
        user = get_user(login_service, user_id=3, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.save_group(Group(id="superman", name="Woman of Steel"))
        actual = login_service.groups.get("superman")
        assert actual is not None
        assert actual.name == "Man of Steel"  # not updated

        # Group admin cannot update another group
        user = get_user(login_service, user_id=2, group_id="superman")
        with pytest.raises(Exception, match="Group name already exists"):
            with current_user_context(user):
                login_service.save_group(Group(id="metropolis", name="Man of Steel"))
        actual = login_service.groups.get("metropolis")
        assert actual is not None
        assert actual.name == "Metropolis"  # not updated

    @with_db_context
    def test_create_user(self, login_service: LoginService) -> None:
        # Site admin can create a user
        user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(user):
            login_service.create_user(UserCreateDTO(name="Laurent", password="S3cr3t"))
        actual = login_service.users.get_by_name("Laurent")
        assert actual is not None
        assert actual.name == "Laurent"

        # Group admin cannot create a user
        user = get_user(login_service, user_id=2, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.create_user(UserCreateDTO(name="Alexandre", password="S3cr3t"))
        actual = login_service.users.get_by_name("Alexandre")
        assert actual is None

    @with_db_context
    def test_save_user(self, login_service: LoginService) -> None:
        # Prepare a new user
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            user = login_service.create_user(UserCreateDTO(name="Laurentius", password="S3cr3t"))

        # Only site admin can update a user
        with current_user_context(admin_user):
            login_service.save_user(User(id=user.id, name="Lawrence"))
        actual = login_service.users.get(user.id)
        assert actual is not None
        assert actual.name == "Lawrence"

        # Group admin cannot update a user
        group_admin_user = get_user(login_service, user_id=2, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(group_admin_user):
                login_service.save_user(User(id=user.id, name="Loran"))
            actual = login_service.users.get(user.id)
            assert actual is not None
            assert actual.name == "Lawrence"

        # A user can update himself
        self_user = get_user(login_service, user_id=user.id)
        with current_user_context(self_user):
            login_service.save_user(User(id=user.id, name="Loran"))
        actual = login_service.users.get(user.id)
        assert actual is not None
        assert actual.name == "Loran"

    @with_db_context
    def test_save_bot(self, login_service: LoginService) -> None:
        # Joh Fredersen can create Maria because he is the leader of Metropolis
        joh_fredersen = get_user(login_service, user_id=4, group_id="metropolis")
        with current_user_context(joh_fredersen):
            login_service.save_bot(BotCreateDTO(name="Maria I", roles=[]))
        actual: t.Sequence[Role] = login_service.bots.get_all_by_owner(4)
        assert len(actual) == 1
        assert actual[0].name == "Maria I"

        # Freder Fredersen can create Maria with the reader role
        freder_fredersen = get_user(login_service, user_id=5, group_id="metropolis")
        with current_user_context(freder_fredersen):
            login_service.save_bot(
                BotCreateDTO(
                    name="Maria II",
                    roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.READER.value)],
                )
            )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create Maria with the admin role
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="Maria III",
                        roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                    )
                )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot with an empty name
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="",
                        roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                    )
                )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot that already exists
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="Maria II",
                        roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                    )
                )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Freder Fredersen cannot create a bot with an invalid group
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="Maria III",
                        roles=[BotRoleCreateDTO(group="metropolis2", role=RoleType.ADMIN.value)],
                    )
                )
        actual = login_service.bots.get_all_by_owner(5)
        assert len(actual) == 1
        assert actual[0].name == "Maria II"

        # Bot's name cannot be empty
        with pytest.raises(Exception, match="Bot name must not be empty"):
            with current_user_context(joh_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="",
                        roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                    )
                )

        # Avoid duplicate bots
        with pytest.raises(Exception, match="Bot name already exists"):
            with current_user_context(joh_fredersen):
                login_service.save_bot(
                    BotCreateDTO(
                        name="Maria I",
                        roles=[BotRoleCreateDTO(group="metropolis", role=RoleType.ADMIN.value)],
                    )
                )

    @with_db_context
    def test_save_role(self, login_service: LoginService) -> None:
        # Prepare a new group and a new user
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        login_service.groups.save(Group(id="web", name="Spider Web"))
        login_service.users.save(User(id=20, name="Spider-man"))
        login_service.users.save(User(id=21, name="Spider-woman"))

        # The site admin can create a role
        with current_user_context(admin_user):
            login_service.save_role(RoleCreationDTO(type=RoleType.ADMIN, group_id="web", identity_id=20))
        actual = login_service.roles.get(20, "web")
        assert actual is not None
        assert actual.type == RoleType.ADMIN

        # The group admin can create a role
        group_admin = get_user(login_service, user_id=20, group_id="web")
        with current_user_context(group_admin):
            login_service.save_role(RoleCreationDTO(type=RoleType.WRITER, group_id="web", identity_id=21))
        actual = login_service.roles.get(21, "web")
        assert actual is not None
        assert actual.type == RoleType.WRITER

        # The group admin cannot create a role with an invalid group
        with pytest.raises(Exception):
            with current_user_context(group_admin):
                login_service.save_role(RoleCreationDTO(type=RoleType.WRITER, group_id="web2", identity_id=21))
        actual = login_service.roles.get(21, "web")
        assert actual is not None
        assert actual.type == RoleType.WRITER

        # The user cannot create a role
        user = get_user(login_service, user_id=21, group_id="web")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.save_role(RoleCreationDTO(type=RoleType.READER, group_id="web", identity_id=20))
        actual = login_service.roles.get(20, "web")
        assert actual is not None
        assert actual.type == RoleType.ADMIN

    @with_db_context
    def test_get_group(self, login_service: LoginService) -> None:
        # Site admin can get any group
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_group("superman")
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin can get his own group
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            actual = login_service.get_group("superman")
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin cannot get another group
        with pytest.raises(GroupNotFoundError):
            with current_user_context(group_admin):
                login_service.get_group("metropolis")

        # Lois Lane can get its own group
        user = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(user):
            actual = login_service.get_group("superman")
        assert actual is not None
        assert actual.id == "superman"

    @with_db_context
    def test_get_group_info(self, login_service: LoginService) -> None:
        # Site admin can get any group
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_group_info("superman")
        assert actual is not None
        assert actual.name == "Superman"
        assert [obj.model_dump() for obj in actual.users] == [
            {"id": 2, "name": "Clark Kent", "role": RoleType.ADMIN},
            {"id": 3, "name": "Lois Lane", "role": RoleType.READER},
        ]

        # Group admin can get his own group
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            actual = login_service.get_group_info("superman")
        assert actual is not None
        assert actual.name == "Superman"

        # Group admin cannot get another group
        with pytest.raises(GroupNotFoundError):
            with current_user_context(group_admin):
                login_service.get_group_info("metropolis")

        # Lois Lane cannot get its own group
        user = get_user(login_service, user_id=3, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.get_group_info("superman")

    @with_db_context
    def test_get_user(self, login_service: LoginService) -> None:
        # Site admin can get any user
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_user(2)
        assert actual is not None
        assert actual.name == "Clark Kent"

        # Group admin can get a user of his own group
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            actual = login_service.get_user(3)
        assert actual is not None
        assert actual.name == "Lois Lane"

        # Group admin cannot get a user of another group
        with current_user_context(group_admin):
            actual = login_service.get_user(5)
        assert actual is None

        # Lois Lane can get its own user
        lois_lane = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(lois_lane):
            actual = login_service.get_user(3)
        assert actual is not None
        assert actual.name == "Lois Lane"

        # Lois Lane is able to create its own bot
        with current_user_context(lois_lane):
            login_service.save_bot(BotCreateDTO(name="Lois bot", roles=[]))

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
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        clark_id = 2
        with current_user_context(admin_user):
            actual = login_service.get_user_info(clark_id)
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
        group_admin = get_user(login_service, user_id=clark_id, group_id="superman")
        lois_id = 3
        with current_user_context(group_admin):
            actual = login_service.get_user_info(lois_id)
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
        freder_id = 5
        with current_user_context(group_admin):
            actual = login_service.get_user_info(freder_id)
        assert actual is None

        # Lois Lane can get its own user info
        lois_lane = get_user(login_service, user_id=lois_id, group_id="superman")
        with current_user_context(lois_lane):
            actual = login_service.get_user_info(lois_id)
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
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="metropolis")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can get any bot
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_bot(joh_bot.id)
        assert actual is not None
        assert actual.name == "Maria"

        # Joh Fredersen can get its own bot
        with current_user_context(joh_fredersen):
            actual = login_service.get_bot(joh_bot.id)
        assert actual is not None
        assert actual.name == "Maria"

        # Freder Fredersen cannot get the bot
        freder_id = 5
        freder_fredersen = get_user(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.get_bot(joh_bot.id)

    @with_db_context
    def test_get_bot_info(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="superman")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can get any bot
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_bot_info(joh_bot.id)
        assert actual is not None
        assert actual.model_dump() == {"id": 6, "isAuthor": True, "name": "Maria", "roles": []}

        # Joh Fredersen can get its own bot
        with current_user_context(joh_fredersen):
            actual = login_service.get_bot_info(joh_bot.id)
        assert actual is not None
        assert actual.model_dump() == {"id": 6, "isAuthor": True, "name": "Maria", "roles": []}

        # Freder Fredersen cannot get the bot
        freder_id = 5
        freder_fredersen = get_user(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.get_bot_info(joh_bot.id)

        # Requesting a fake bot fails
        with pytest.raises(Exception):
            with current_user_context(admin_user):
                login_service.get_bot_info(999)

    @with_db_context
    def test_get_all_bots_by_owner(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="superman")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can get any bot
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_all_bots_by_owner(joh_id)
        expected = [{"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id}]
        assert [obj.to_dto().model_dump() for obj in actual] == expected

        # Joh Fredersen can get its own bot
        with current_user_context(joh_fredersen):
            actual = login_service.get_all_bots_by_owner(joh_id)
        expected = [{"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id}]
        assert [obj.to_dto().model_dump() for obj in actual] == expected

        # Freder Fredersen cannot get the bot
        freder_id = 5
        freder_fredersen = get_user(login_service, user_id=freder_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(freder_fredersen):
                login_service.get_all_bots_by_owner(joh_id)

    @with_db_context
    def test_exists_bot(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="superman")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

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
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="superman")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

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
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_all_groups()
        assert [g.model_dump() for g in actual] == [
            {"id": "admin", "name": "X-Men"},
            {"id": "superman", "name": "Superman"},
            {"id": "metropolis", "name": "Metropolis"},
        ]

        # The group admin can its own groups
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            actual = login_service.get_all_groups()
        assert [g.model_dump() for g in actual] == [{"id": "superman", "name": "Superman"}]

        # The user can get its own groups
        user = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(user):
            actual = login_service.get_all_groups()
        assert [g.model_dump() for g in actual] == [{"id": "superman", "name": "Superman"}]

    @with_db_context
    def test_get_all_users(self, login_service: LoginService, db_session: Session) -> None:
        # The site admin can get all users
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            # Without details
            with DBStatementRecorder(db_session.bind) as db_recorder:
                actual = login_service.get_all_users()
            assert len(db_recorder.sql_statements) == 1  # Only one request to get all users
            assert [u.model_dump() for u in actual] == [
                {"id": 1, "name": "Professor Xavier"},
                {"id": 2, "name": "Clark Kent"},
                {"id": 3, "name": "Lois Lane"},
                {"id": 4, "name": "Joh Fredersen"},
                {"id": 5, "name": "Freder Fredersen"},
            ]
            # With details
            with DBStatementRecorder(db_session.bind) as db_recorder:
                actual = login_service.get_all_users(details=True)
            assert len(db_recorder.sql_statements) == 2
            # One request to get all users
            # One request to get all roles
            assert [u.model_dump() for u in actual] == [
                {
                    "id": 1,
                    "name": "Professor Xavier",
                    "roles": [{"group_id": "admin", "group_name": "X-Men", "identity_id": 1, "type": RoleType.ADMIN}],
                },
                {
                    "id": 2,
                    "name": "Clark Kent",
                    "roles": [
                        {"group_id": "superman", "group_name": "Superman", "identity_id": 2, "type": RoleType.ADMIN}
                    ],
                },
                {
                    "id": 3,
                    "name": "Lois Lane",
                    "roles": [
                        {"group_id": "superman", "group_name": "Superman", "identity_id": 3, "type": RoleType.READER}
                    ],
                },
                {
                    "id": 4,
                    "name": "Joh Fredersen",
                    "roles": [
                        {"group_id": "metropolis", "group_name": "Metropolis", "identity_id": 4, "type": RoleType.ADMIN}
                    ],
                },
                {
                    "id": 5,
                    "name": "Freder Fredersen",
                    "roles": [
                        {
                            "group_id": "metropolis",
                            "group_name": "Metropolis",
                            "identity_id": 5,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ]

        # The group admin can get its own users, and that's all
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            # Without details
            with DBStatementRecorder(db_session.bind) as db_recorder:
                actual = login_service.get_all_users()
            assert len(db_recorder.sql_statements) == 3
            # One request to get the current user groups
            # One request for users
            # One request for roles
            assert [u.model_dump() for u in actual] == [{"id": 2, "name": "Clark Kent"}, {"id": 3, "name": "Lois Lane"}]

            # With details
            with DBStatementRecorder(db_session.bind) as db_recorder:
                actual = login_service.get_all_users(details=True)
            assert len(db_recorder.sql_statements) == 3  # Same requests
            assert [u.model_dump() for u in actual] == [
                {
                    "id": 2,
                    "name": "Clark Kent",
                    "roles": [
                        {"group_id": "superman", "group_name": "Superman", "identity_id": 2, "type": RoleType.ADMIN}
                    ],
                },
                {
                    "id": 3,
                    "name": "Lois Lane",
                    "roles": [
                        {"group_id": "superman", "group_name": "Superman", "identity_id": 3, "type": RoleType.READER}
                    ],
                },
            ]

        # Same check as group owner
        user = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(user):
            actual = login_service.get_all_users()
        assert [u.model_dump() for u in actual] == [{"id": 2, "name": "Clark Kent"}, {"id": 3, "name": "Lois Lane"}]

    @with_db_context
    def test_get_all_bots(self, login_service: LoginService) -> None:
        # Create a bot for Joh Fredersen
        joh_id = 4
        joh_fredersen = get_user(login_service, user_id=joh_id, group_id="superman")
        with current_user_context(joh_fredersen):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can get all bots
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_all_bots()
        assert [b.to_dto().model_dump() for b in actual] == [
            {"id": joh_bot.id, "is_author": True, "name": "Maria", "owner": joh_id},
        ]

        # The group admin cannot access the list of bots
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_bots()

        # The user cannot access the list of bots
        user = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(user):
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_bots()

    @with_db_context
    def test_get_all_roles_in_group(self, login_service: LoginService) -> None:
        # The site admin can get all roles in a given group
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            actual = login_service.get_all_roles_in_group("superman")
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
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with current_user_context(group_admin):
            actual = login_service.get_all_roles_in_group("superman")
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
        user = get_user(login_service, user_id=3, group_id="superman")
        with current_user_context(user):
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_roles_in_group("superman")

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
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            login_service.delete_group("g1")
        assert login_service.groups.get(group1.id) is None

        # The group admin can delete his own group
        group_admin = get_user(login_service, user_id=3, group_id="g2")
        with current_user_context(group_admin):
            login_service.delete_group("g2")
        assert login_service.groups.get(group2.id) is None

        # The user cannot delete a group
        user = get_user(login_service, user_id=5, group_id="g3")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.delete_group("g3")
        assert login_service.groups.get(group3.id) is not None

    @with_db_context
    def test_delete_user(self, login_service: LoginService) -> None:
        # Create Joh's bot
        joh_id = 4
        joh_user = get_user(login_service, user_id=joh_id, group_id="metropolis")
        with current_user_context(joh_user):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can delete Fredersen (5)
        freder_id = 5
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            login_service.delete_user(freder_id)
        assert login_service.users.get(freder_id) is None

        # The group admin Joh can delete himself (4)
        with current_user_context(joh_user):
            login_service.delete_user(joh_id)
        assert login_service.users.get(joh_id) is None
        assert login_service.bots.get(joh_bot.id) is None

        # Lois Lane cannot delete Clark Kent (2)
        lois_id = 3
        clark_id = 2
        lois = get_user(login_service, user_id=lois_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(lois):
                login_service.delete_user(clark_id)
        assert login_service.users.get(clark_id) is not None

        # Clark Kent cannot delete Lois Lane (3)
        clark = get_user(login_service, user_id=clark_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(clark):
                login_service.delete_user(lois_id)
        assert login_service.users.get(lois_id) is not None

    @with_db_context
    def test_delete_bot(self, login_service: LoginService) -> None:
        # Create Joh's bot
        joh_id = 4
        joh_user = get_user(login_service, user_id=joh_id, group_id="metropolis")
        with current_user_context(joh_user):
            joh_bot = login_service.save_bot(BotCreateDTO(name="Maria", roles=[]))

        # The site admin can delete the bot
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            login_service.delete_bot(joh_bot.id)
        assert login_service.bots.get(joh_bot.id) is None

        # Create Lois's bot
        lois_id = 3
        lois = get_user(login_service, user_id=lois_id, group_id="superman")
        with current_user_context(lois):
            lois_bot = login_service.save_bot(BotCreateDTO(name="Lois bot", roles=[]))

        # The group admin cannot delete the bot
        clark_id = 2
        clark = get_user(login_service, user_id=clark_id, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(clark):
                login_service.delete_bot(lois_bot.id)
        assert login_service.bots.get(lois_bot.id) is not None

        # Create Freder's bot
        freder_id = 5
        user = get_user(login_service, user_id=freder_id, group_id="metropolis")
        with current_user_context(user):
            freder_bot = login_service.save_bot(BotCreateDTO(name="Freder bot", roles=[]))

        # Freder can delete his own bot
        with current_user_context(user):
            login_service.delete_bot(freder_bot.id)
        assert login_service.bots.get(freder_bot.id) is None

        # Freder cannot delete Lois's bot
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.delete_bot(lois_bot.id)
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
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            login_service.delete_role(role.identity.id, role.group.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin can delete a role of his own group
        group_admin = get_user(login_service, user_id=user.id, group_id="g1")
        with current_user_context(group_admin):
            login_service.delete_role(role.identity.id, role.group.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin cannot delete a role of another group
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(group_admin):
                login_service.delete_role(role.identity.id, "g1")
        assert login_service.roles.get(role.identity.id, "g1") is not None

        # The user cannot delete a role
        user = get_user(login_service, user_id=1, group_id="g1")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(user):
                login_service.delete_role(role.identity.id, role.group.id)
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
        admin_user = get_user(login_service, user_id=ADMIN_ID, group_id="admin")
        with current_user_context(admin_user):
            login_service.delete_all_roles_from_user(user.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin can delete a role of his own group
        group_admin = get_user(login_service, user_id=user.id, group_id="g1")
        with current_user_context(group_admin):
            login_service.delete_all_roles_from_user(user.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is None

        # Create a new role
        role = login_service.roles.save(Role(type=RoleType.ADMIN, group=group, identity=user))

        # The group admin cannot delete a role of another group
        group_admin = get_user(login_service, user_id=2, group_id="superman")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(group_admin):
                login_service.delete_all_roles_from_user(user.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is not None

        # The user cannot delete a role
        user = get_user(login_service, user_id=1, group_id="g1")
        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(group_admin):
                login_service.delete_all_roles_from_user(user.id)
        assert login_service.roles.get(role.identity.id, role.group.id) is not None
