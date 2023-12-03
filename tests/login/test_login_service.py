import typing as t
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.login.model import (
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

SITE_ADMIN = RequestParameters(
    user=JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
)

GROUP_ADMIN = RequestParameters(
    user=JWTUser(
        id=1,
        impersonator=1,
        type="users",
        groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
    )
)

USER3 = RequestParameters(
    user=JWTUser(
        id=3,
        impersonator=3,
        type="users",
        groups=[JWTGroup(id="group", name="group", role=RoleType.READER)],
    )
)

BAD_PARAM = RequestParameters(user=None)


class TestLoginService:
    """
    Test login service.

    important:

    - the `GroupRepository` insert an admin group in the database if it does not exist:
      `Group(id="admin", name="admin")`

    - the `UserRepository` insert an admin user in the database if it does not exist.
      `User(id=1, name="admin", password=Password(config.security.admin_pwd))`

    - the `RoleRepository` insert an admin role in the database if it does not exist.
      `Role(type=RoleType.ADMIN, identity=User(id=1), group=Group(id="admin"))`
    """

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_create", [(SITE_ADMIN, True), (GROUP_ADMIN, True), (USER3, False), (BAD_PARAM, False)]
    )
    def test_save_group(self, login_service: LoginService, param: RequestParameters, can_create: bool) -> None:
        group = Group(id="group", name="group")

        # Only site admin and group admin can update a group
        if can_create:
            actual = login_service.save_group(group, param)
            assert actual == group
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.save_group(group, param)
            actual = login_service.groups.get(group.id)
            assert actual is None

        # Users can't create a duplicate group
        with pytest.raises(HTTPException):
            login_service.save_group(group, param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_create", [(SITE_ADMIN, True), (GROUP_ADMIN, False), (USER3, False), (BAD_PARAM, False)]
    )
    def test_create_user(self, login_service: LoginService, param: RequestParameters, can_create: bool) -> None:
        create = UserCreateDTO(name="hello", password="world")

        # Only site admin can create a user
        if can_create:
            actual = login_service.create_user(create, param)
            assert actual.name == create.name
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.create_user(create, param)
            actual = login_service.users.get_by_name(create.name)
            assert actual is None

        # Users can't create a duplicate user
        with pytest.raises(HTTPException):
            login_service.create_user(create, param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_save",
        [
            # (SITE_ADMIN, True),
            (GROUP_ADMIN, False),
            # (USER3, False),
            # (BAD_PARAM, False),
        ],
    )
    def test_save_user(self, login_service: LoginService, param: RequestParameters, can_save: bool) -> None:
        create = UserCreateDTO(name="Laurent", password="S3cr3t")
        user = login_service.create_user(create, SITE_ADMIN)
        user.name = "Roland"

        # Only site admin can update a user
        if can_save:
            login_service.save_user(user, param)
            actual = login_service.users.get_by_name(user.name)
            assert actual == user
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.save_user(user, param)
            actual = login_service.users.get_by_name(user.name)
            assert actual != user

    @with_db_context
    def test_save_user__themselves(self, login_service: LoginService) -> None:
        user_create = UserCreateDTO(name="Laurent", password="S3cr3t")
        user = login_service.create_user(user_create, SITE_ADMIN)

        # users can update themselves
        param = RequestParameters(
            user=JWTUser(
                id=user.id,
                impersonator=user.id,
                type="users",
                groups=[JWTGroup(id="group", name="group", role=RoleType.READER)],
            )
        )
        user.name = "Roland"
        actual = login_service.save_user(user, param)
        assert actual == user

    @with_db_context
    def test_save_bot(self, login_service: LoginService) -> None:
        # Prepare the user3 in the db
        assert USER3.user is not None
        user3 = User(id=USER3.user.id, name="Scoobydoo")
        login_service.users.save(user3)

        # Prepare the user group and role
        for jwt_group in USER3.user.groups:
            group = Group(id=jwt_group.id, name=jwt_group.name)
            login_service.groups.save(group)
            role = Role(type=jwt_group.role, identity=user3, group=group)
            login_service.roles.save(role)

        # Request parameters must reference a user
        with pytest.raises(HTTPException):
            login_service.save_bot(BotCreateDTO(name="bot", roles=[]), BAD_PARAM)

        # The user USER3 is a reader in the group "group" and can crate a bot with the same role
        assert all(jwt_group.role == RoleType.READER for jwt_group in USER3.user.groups)
        bot_create = BotCreateDTO(name="bot", roles=[BotRoleCreateDTO(group="group", role=RoleType.READER.value)])
        bot = login_service.save_bot(bot_create, USER3)

        assert bot.name == bot_create.name
        assert bot.owner == USER3.user.id
        assert bot.is_author is True

        # The user can't create a bot with an empty name
        bot_create = BotCreateDTO(name="", roles=[BotRoleCreateDTO(group="group", role=RoleType.READER.value)])
        with pytest.raises(HTTPException):
            login_service.save_bot(bot_create, USER3)

        # The user can't create a bot with a higher role than his own
        for role_type in set(RoleType) - {RoleType.READER}:
            bot_create = BotCreateDTO(name="bot", roles=[BotRoleCreateDTO(group="group", role=role_type.value)])
            with pytest.raises(UserHasNotPermissionError):
                login_service.save_bot(bot_create, USER3)

        # The user can't create a bot that already exists
        bot_create = BotCreateDTO(name="bot", roles=[BotRoleCreateDTO(group="group", role=RoleType.READER.value)])
        with pytest.raises(HTTPException):
            login_service.save_bot(bot_create, USER3)

        # The user can't create a bot with a group that does not exist
        bot_create = BotCreateDTO(name="bot", roles=[BotRoleCreateDTO(group="unknown", role=RoleType.READER.value)])
        with pytest.raises(HTTPException):
            login_service.save_bot(bot_create, USER3)

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_save", [(SITE_ADMIN, True), (GROUP_ADMIN, True), (USER3, False), (BAD_PARAM, False)]
    )
    def test_save_role(self, login_service: LoginService, param: RequestParameters, can_save: bool) -> None:
        # Prepare the site admin in the db
        assert SITE_ADMIN.user is not None
        admin = User(id=SITE_ADMIN.user.id, name="Superman")
        login_service.users.save(admin)

        # Prepare the group "group" in the db
        # noinspection SpellCheckingInspection
        group = Group(id="group", name="Kryptonians")
        login_service.groups.save(group)

        # Only site admin and group admin can update a role
        role = RoleCreationDTO(type=RoleType.ADMIN, identity_id=0, group_id="group")
        if can_save:
            actual = login_service.save_role(role, param)
            assert actual.type == RoleType.ADMIN
            assert actual.identity == admin
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.save_role(role, param)
            actual = login_service.roles.get_all_by_group(group.id)
            assert len(actual) == 0

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_get", [(SITE_ADMIN, True), (GROUP_ADMIN, True), (USER3, True), (BAD_PARAM, False)]
    )
    def test_get_group(self, login_service: LoginService, param: RequestParameters, can_get: bool) -> None:
        # Prepare the group "group" in the db
        # noinspection SpellCheckingInspection
        group = Group(id="group", name="Vulcans")
        login_service.groups.save(group)

        # Anybody except anonymous can get a group
        if can_get:
            actual = login_service.get_group("group", param)
            assert actual == group
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_group(group.id, param)

    # noinspection SpellCheckingInspection
    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (
                SITE_ADMIN,
                {
                    "id": "group",
                    "name": "Vulcans",
                    "users": [
                        {"id": 3, "name": "Spock", "role": RoleType.RUNNER},
                        {"id": 4, "name": "Saavik", "role": RoleType.RUNNER},
                    ],
                },
            ),
            (
                GROUP_ADMIN,
                {
                    "id": "group",
                    "name": "Vulcans",
                    "users": [
                        {"id": 3, "name": "Spock", "role": RoleType.RUNNER},
                        {"id": 4, "name": "Saavik", "role": RoleType.RUNNER},
                    ],
                },
            ),
            (USER3, {}),
            (BAD_PARAM, {}),
        ],
    )
    def test_get_group_info(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Mapping[str, t.Any],
    ) -> None:
        # Prepare the group "group" in the db
        # noinspection SpellCheckingInspection
        group = Group(id="group", name="Vulcans")
        login_service.groups.save(group)

        # Prepare the user3 in the db
        assert USER3.user is not None
        user3 = User(id=USER3.user.id, name="Spock")
        login_service.users.save(user3)

        # Prepare an LDAP user named "Jane" with id=4
        user4 = UserLdap(id=4, name="Saavik")
        login_service.users.save(user4)

        # Spock and Saavik are vulcans and can run simulations
        role = Role(type=RoleType.RUNNER, identity=user3, group=group)
        login_service.roles.save(role)
        role = Role(type=RoleType.RUNNER, identity=user4, group=group)
        login_service.roles.save(role)

        # Only site admin and group admin can get a group info
        if expected:
            actual = login_service.get_group_info("group", param)
            assert actual.dict() == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_group_info(group.id, param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_get", [(SITE_ADMIN, True), (GROUP_ADMIN, True), (USER3, True), (BAD_PARAM, False)]
    )
    def test_get_user(self, login_service: LoginService, param: RequestParameters, can_get: bool) -> None:
        # Prepare a group of readers
        group = Group(id="group", name="readers")
        login_service.groups.save(group)

        # The user3 is a reader in the group "group"
        user3 = User(id=USER3.user.id, name="Batman")
        login_service.users.save(user3)
        role = Role(type=RoleType.READER, identity=user3, group=group)
        login_service.roles.save(role)

        # Anybody except anonymous can get the user3
        if can_get:
            actual = login_service.get_user(user3.id, param)
            assert actual == user3
        else:
            # This function doesn't raise an exception if the user does not exist
            actual = login_service.get_user(user3.id, param)
            assert actual is None

    @with_db_context
    def test_get_identity(self, login_service: LoginService) -> None:
        # important: id=1 is the admin user
        user = login_service.users.save(User(id=2, name="John"))
        user_ldap = login_service.users.save(UserLdap(id=3, name="Jane"))
        bot = login_service.users.save(Bot(id=4, name="my-app", owner=3, is_author=False))

        assert login_service.get_identity(2, include_token=False) == user
        assert login_service.get_identity(3, include_token=False) == user_ldap
        assert login_service.get_identity(4, include_token=False) is None

        assert login_service.get_identity(2, include_token=True) == user
        assert login_service.get_identity(3, include_token=True) == user_ldap
        assert login_service.get_identity(4, include_token=True) == bot

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (
                SITE_ADMIN,
                {
                    "id": 3,
                    "name": "Batman",
                    "roles": [
                        {
                            "group_id": "group",
                            "group_name": "readers",
                            "identity_id": 3,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ),
            (
                GROUP_ADMIN,
                {
                    "id": 3,
                    "name": "Batman",
                    "roles": [
                        {
                            "group_id": "group",
                            "group_name": "readers",
                            "identity_id": 3,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ),
            (
                USER3,
                {
                    "id": 3,
                    "name": "Batman",
                    "roles": [
                        {
                            "group_id": "group",
                            "group_name": "readers",
                            "identity_id": 3,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ),
            (BAD_PARAM, {}),
        ],
    )
    def test_get_user_info(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Mapping[str, t.Any],
    ) -> None:
        # Prepare a group of readers
        group = Group(id="group", name="readers")
        login_service.groups.save(group)

        # The user3 is a reader in the group "group"
        user3 = User(id=USER3.user.id, name="Batman")
        login_service.users.save(user3)
        role = Role(type=RoleType.READER, identity=user3, group=group)
        login_service.roles.save(role)

        # Anybody except anonymous can get the user3
        if expected:
            actual = login_service.get_user_info(user3.id, param)
            assert actual.dict() == expected
        else:
            # This function doesn't raise an exception if the user does not exist
            actual = login_service.get_user_info(user3.id, param)
            assert actual is None

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_get", [(SITE_ADMIN, True), (GROUP_ADMIN, False), (USER3, True), (BAD_PARAM, False)]
    )
    def test_get_bot(self, login_service: LoginService, param: RequestParameters, can_get: bool) -> None:
        # Prepare a user in the db, with id=4
        clark = User(id=3, name="Clark")
        login_service.users.save(clark)

        # Prepare a bot in the db (using the ID or user3)
        bot = Bot(id=4, name="Maria", owner=clark.id, is_author=True)
        login_service.users.save(bot)

        # Only site admin and the owner can get a bot
        if can_get:
            actual = login_service.get_bot(bot.id, param)
            assert actual == bot
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_bot(bot.id, param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (
                SITE_ADMIN,
                {
                    "id": 4,
                    "isAuthor": True,
                    "name": "Maria",
                    "roles": [
                        {
                            "group_id": "Metropolis",
                            "group_name": "watchers",
                            "identity_id": 4,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ),
            (GROUP_ADMIN, {}),
            (
                USER3,
                {
                    "id": 4,
                    "isAuthor": True,
                    "name": "Maria",
                    "roles": [
                        {
                            "group_id": "Metropolis",
                            "group_name": "watchers",
                            "identity_id": 4,
                            "type": RoleType.READER,
                        }
                    ],
                },
            ),
            (BAD_PARAM, {}),
        ],
    )
    def test_get_bot_info(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Mapping[str, t.Any],
    ) -> None:
        # Prepare a user in the db, with id=4
        clark = User(id=3, name="Clark")
        login_service.users.save(clark)

        # Prepare a bot in the db (using the ID or user3)
        bot = Bot(id=4, name="Maria", owner=clark.id, is_author=True)
        login_service.users.save(bot)

        # Prepare a group of readers
        group = Group(id="Metropolis", name="watchers")
        login_service.groups.save(group)

        # The user3 is a reader in the group "group"
        role = Role(type=RoleType.READER, identity=bot, group=group)
        login_service.roles.save(role)

        # Only site admin and the owner can get a bot
        if expected:
            actual = login_service.get_bot_info(bot.id, param)
            assert actual is not None
            assert actual.dict() == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_bot_info(bot.id, param)

    @with_db_context
    @pytest.mark.parametrize("param, expected", [(SITE_ADMIN, [5]), (GROUP_ADMIN, []), (USER3, [5]), (BAD_PARAM, [])])
    def test_get_all_bots_by_owner(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Mapping[str, t.Any],
    ) -> None:
        # add a user, an LDAP user and a bot in the db
        user = User(id=3, name="John")
        login_service.users.save(user)
        user_ldap = UserLdap(id=4, name="Jane")
        login_service.users.save(user_ldap)
        bot = Bot(id=5, name="my-app", owner=3, is_author=False)
        login_service.users.save(bot)

        if expected:
            actual = login_service.get_all_bots_by_owner(3, param)
            assert [b.id for b in actual] == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_bots_by_owner(3, param)

    @with_db_context
    def test_exists_bot(self, login_service: LoginService) -> None:
        # Prepare the user3 in the db
        assert USER3.user is not None
        user3 = User(id=USER3.user.id, name="Clark")
        login_service.users.save(user3)

        # Prepare a bot in the db (using the ID or user3)
        bot = Bot(id=4, name="Maria", owner=user3.id, is_author=True)
        login_service.users.save(bot)

        # Everybody can check the existence of a bot
        assert login_service.exists_bot(4)
        assert not login_service.exists_bot(5)  # unknown ID
        assert not login_service.exists_bot(3)  # user ID, not bot ID

    @with_db_context
    def test_authenticate__unknown_user(self, login_service: LoginService) -> None:
        # An unknown user cannot log in
        user = login_service.authenticate(name="unknown", pwd="S3cr3t")
        assert user is None

    @with_db_context
    def test_authenticate__known_user(self, login_service: LoginService) -> None:
        # Create a user named "Tarzan" in the group "Adventure"
        group = Group(id="adventure", name="Adventure")
        login_service.groups.save(group)
        user = User(id=3, name="Tarzan", password=Password("S3cr3t"))
        login_service.users.save(user)
        role = Role(type=RoleType.READER, identity=user, group=group)
        login_service.roles.save(role)

        # A known user can log in
        jwt_user = login_service.authenticate(name="Tarzan", pwd="S3cr3t")
        assert jwt_user is not None
        assert jwt_user.id == user.id
        assert jwt_user.impersonator == user.id
        assert jwt_user.type == "users"
        assert jwt_user.groups == [JWTGroup(id="adventure", name="Adventure", role=RoleType.READER)]

    @with_db_context
    def test_authenticate__external_user(self, login_service: LoginService) -> None:
        # Create a user named "Tarzan"
        user_ldap = UserLdap(id=3, name="Tarzan", external_id="tarzan", firstname="Tarzan", lastname="Jungle")
        login_service.users.save(user_ldap)

        # Mock the LDAP service
        login_service.ldap.login = Mock(return_value=user_ldap)  # type: ignore
        login_service.ldap.get = Mock(return_value=user_ldap)  # type: ignore

        # A known user can log in
        jwt_user = login_service.authenticate(name="Tarzan", pwd="S3cr3t")
        assert jwt_user is not None
        assert jwt_user.id == user_ldap.id
        assert jwt_user.impersonator == user_ldap.id
        assert jwt_user.type == "users_ldap"
        assert jwt_user.groups == []

    @with_db_context
    def test_get_jwt(self, login_service: LoginService) -> None:
        # Prepare the user3 in the db
        assert USER3.user is not None
        user3 = User(id=USER3.user.id, name="Clark")
        login_service.users.save(user3)

        # Attach a group to the user
        group = Group(id="group", name="readers")
        login_service.groups.save(group)
        role = Role(type=RoleType.READER, identity=user3, group=group)
        login_service.roles.save(role)

        # Prepare an LDAP user in the db
        user_ldap = UserLdap(id=4, name="Jane")
        login_service.users.save(user_ldap)

        # Prepare a bot in the db (using the ID or user3)
        bot = Bot(id=5, name="Maria", owner=user3.id, is_author=True)
        login_service.users.save(bot)

        # We can get a JWT for a user, an LDAP user, but not a bot
        jwt_user = login_service.get_jwt(user3.id)
        assert jwt_user is not None
        assert jwt_user.id == user3.id
        assert jwt_user.impersonator == user3.id
        assert jwt_user.type == "users"
        assert jwt_user.groups == [JWTGroup(id="group", name="readers", role=RoleType.READER)]

        jwt_user = login_service.get_jwt(user_ldap.id)
        assert jwt_user is not None
        assert jwt_user.id == user_ldap.id
        assert jwt_user.impersonator == user_ldap.id
        assert jwt_user.type == "users_ldap"
        assert jwt_user.groups == []

        jwt_user = login_service.get_jwt(bot.id)
        assert jwt_user is None

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (
                SITE_ADMIN,
                [
                    {"id": "admin", "name": "admin"},
                    {"id": "gr1", "name": "Adventure"},
                    {"id": "gr2", "name": "Comedy"},
                ],
            ),
            (
                GROUP_ADMIN,
                [
                    {"id": "admin", "name": "admin"},
                    {"id": "gr2", "name": "Comedy"},
                ],
            ),
            (
                USER3,
                [
                    {"id": "gr1", "name": "Adventure"},
                ],
            ),
            (BAD_PARAM, []),
        ],
    )
    def test_get_all_groups(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Sequence[t.Mapping[str, str]],
    ) -> None:
        # Prepare some groups in the db
        group1 = Group(id="gr1", name="Adventure")
        login_service.groups.save(group1)
        group2 = Group(id="gr2", name="Comedy")
        login_service.groups.save(group2)

        # The group admin is a reader in the group "gr2"
        assert GROUP_ADMIN.user is not None
        robin_hood = User(id=GROUP_ADMIN.user.id, name="Robin")
        login_service.users.save(robin_hood)
        role = Role(type=RoleType.READER, identity=robin_hood, group=group2)
        login_service.roles.save(role)

        # The user3 is a reader in the group "gr1"
        assert USER3.user is not None
        indiana_johns = User(id=USER3.user.id, name="Indiana")
        login_service.users.save(indiana_johns)
        role = Role(type=RoleType.READER, identity=indiana_johns, group=group1)
        login_service.roles.save(role)

        # Anybody except anonymous can get the list of groups
        if expected:
            # The site admin can see all groups
            actual = login_service.get_all_groups(param)
            assert [g.dict() for g in actual] == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_groups(param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (
                SITE_ADMIN,
                [
                    {"id": 0, "name": "Superman"},
                    {"id": 1, "name": "John"},
                    {"id": 2, "name": "Jane"},
                    {"id": 3, "name": "Tarzan"},
                ],
            ),
            (
                GROUP_ADMIN,
                [
                    {"id": 1, "name": "John"},
                ],
            ),
            (
                USER3,
                [
                    {"id": 3, "name": "Tarzan"},
                ],
            ),
            (BAD_PARAM, []),
        ],
    )
    def test_get_all_users(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Sequence[t.Mapping[str, t.Union[int, str]]],
    ) -> None:
        # Insert some users in the db
        user0 = User(id=0, name="Superman")
        login_service.users.save(user0)
        user1 = User(id=1, name="John")
        login_service.users.save(user1)
        user2 = User(id=2, name="Jane")
        login_service.users.save(user2)
        user3 = User(id=3, name="Tarzan")
        login_service.users.save(user3)

        # user3 is a reader in the group "group"
        group = Group(id="group", name="readers")
        login_service.groups.save(group)
        role = Role(type=RoleType.READER, identity=user3, group=group)
        login_service.roles.save(role)

        # Anybody except anonymous can get the list of users
        if expected:
            actual = login_service.get_all_users(param)
            assert [u.dict() for u in actual] == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_users(param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (SITE_ADMIN, [5]),
            (GROUP_ADMIN, []),
            (USER3, []),
            (BAD_PARAM, []),
        ],
    )
    def test_get_all_bots(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Sequence[int],
    ) -> None:
        # add a user, an LDAP user and a bot in the db
        user = User(id=3, name="John")
        login_service.users.save(user)
        user_ldap = UserLdap(id=4, name="Jane")
        login_service.users.save(user_ldap)
        bot = Bot(id=5, name="my-app", owner=3, is_author=False)
        login_service.users.save(bot)

        if expected:
            actual = login_service.get_all_bots(param)
            assert [b.id for b in actual] == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_bots(param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, expected",
        [
            (SITE_ADMIN, [(3, "group")]),
            (GROUP_ADMIN, [(3, "group")]),
            (USER3, []),
            (BAD_PARAM, []),
        ],
    )
    def test_get_all_roles_in_group(
        self,
        login_service: LoginService,
        param: RequestParameters,
        expected: t.Sequence[t.Tuple[int, str]],
    ) -> None:
        # Insert some users in the db
        user0 = User(id=0, name="Superman")
        login_service.users.save(user0)
        user1 = User(id=1, name="John")
        login_service.users.save(user1)
        user2 = User(id=2, name="Jane")
        login_service.users.save(user2)
        user3 = User(id=3, name="Tarzan")
        login_service.users.save(user3)

        # user3 is a reader in the group "group"
        group = Group(id="group", name="readers")
        login_service.groups.save(group)
        role = Role(type=RoleType.READER, identity=user3, group=group)
        login_service.roles.save(role)

        # The site admin and the group admin can get the list of roles in a group
        if expected:
            actual = login_service.get_all_roles_in_group("group", param)
            assert [(r.identity_id, r.group_id) for r in actual] == expected
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.get_all_roles_in_group("group", param)

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_delete",
        [
            (SITE_ADMIN, True),
            (GROUP_ADMIN, True),
            (USER3, False),
            (BAD_PARAM, False),
        ],
    )
    def test_delete_group(self, login_service: LoginService, param: RequestParameters, can_delete: bool) -> None:
        # Insert a group in the db
        group = Group(id="group", name="readers")
        login_service.groups.save(group)

        # The site admin and the group admin can delete a group
        if can_delete:
            login_service.delete_group("group", param)
            actual = login_service.groups.get("group")
            assert actual is None
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.delete_group("group", param)
            actual = login_service.groups.get("group")
            assert actual is not None

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_delete",
        [
            (SITE_ADMIN, True),
            (GROUP_ADMIN, False),
            (USER3, False),
            (BAD_PARAM, False),
        ],
    )
    def test_delete_user(self, login_service: LoginService, param: RequestParameters, can_delete: bool) -> None:
        # Insert a user in the db which is an owner of a bot
        user = User(id=3, name="John")
        login_service.users.save(user)
        bot = Bot(id=4, name="my-app", owner=3, is_author=False)
        login_service.users.save(bot)

        # The site admin can delete the user
        if can_delete:
            login_service.delete_user(3, param)
            actual = login_service.users.get(3)
            assert actual is None
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.delete_user(3, param)
            actual = login_service.users.get(3)
            assert actual is not None

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_delete",
        [
            (SITE_ADMIN, True),
            (GROUP_ADMIN, False),
            (USER3, True),
            (BAD_PARAM, False),
        ],
    )
    def test_delete_bot(self, login_service: LoginService, param: RequestParameters, can_delete: bool) -> None:
        # Insert a user in the db which is an owner of a bot
        user = User(id=3, name="John")
        login_service.users.save(user)
        bot = Bot(id=4, name="my-app", owner=3, is_author=False)
        login_service.users.save(bot)

        # The site admin and the current owner can delete the bot
        if can_delete:
            login_service.delete_bot(4, param)
            actual = login_service.bots.get(4)
            assert actual is None
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.delete_bot(4, param)
            actual = login_service.bots.get(4)
            assert actual is not None

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_delete",
        [
            (SITE_ADMIN, True),
            (GROUP_ADMIN, True),
            (USER3, False),
            (BAD_PARAM, False),
        ],
    )
    def test_delete_role(self, login_service: LoginService, param: RequestParameters, can_delete: bool) -> None:
        # Insert the user3 in the db
        user = User(id=3, name="Tarzan")
        login_service.users.save(user)

        # Insert a group in the db
        group = Group(id="group", name="readers")
        login_service.groups.save(group)

        # Insert a role in the db
        role = Role(type=RoleType.READER, identity=user, group=group)
        login_service.roles.save(role)

        # The site admin and the group admin can delete a role
        if can_delete:
            login_service.delete_role(3, "group", param)
            actual = login_service.roles.get_all_by_group("group")
            assert len(actual) == 0
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.delete_role(3, "group", param)
            actual = login_service.roles.get_all_by_group("group")
            assert len(actual) == 1

    @with_db_context
    @pytest.mark.parametrize(
        "param, can_delete",
        [
            (SITE_ADMIN, True),
            (GROUP_ADMIN, True),
            (USER3, False),
            (BAD_PARAM, False),
        ],
    )
    def test_delete_all_roles_from_user(
        self, login_service: LoginService, param: RequestParameters, can_delete: bool
    ) -> None:
        # Insert the user3 in the db
        assert USER3.user is not None
        user = User(id=USER3.user.id, name="Tarzan")
        login_service.users.save(user)

        # Insert a group in the db
        group = Group(id="group", name="readers")
        login_service.groups.save(group)

        # Insert a role in the db
        role = Role(type=RoleType.READER, identity=user, group=group)
        login_service.roles.save(role)

        # Insert the group admin in the db
        assert GROUP_ADMIN.user is not None
        group_admin = User(id=GROUP_ADMIN.user.id, name="John")
        login_service.users.save(group_admin)

        # Insert another group in the db
        group2 = Group(id="group2", name="readers")
        login_service.groups.save(group2)

        # Insert a role in the db
        role2 = Role(type=RoleType.READER, identity=group_admin, group=group2)
        login_service.roles.save(role2)

        # The site admin and the group admin can delete a role
        if can_delete:
            login_service.delete_all_roles_from_user(3, param)
            actual = login_service.roles.get_all_by_group("group")
            assert len(actual) == 0
            actual = login_service.roles.get_all_by_group("group2")
            assert len(actual) == 1
        else:
            with pytest.raises(UserHasNotPermissionError):
                login_service.delete_all_roles_from_user(3, param)
            actual = login_service.roles.get_all_by_group("group")
            assert len(actual) == 1
            actual = login_service.roles.get_all_by_group("group2")
            assert len(actual) == 1
