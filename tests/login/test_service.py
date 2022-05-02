from typing import Any, Callable, List, Tuple
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.ldap import LdapService
from antarest.login.model import (
    User,
    Password,
    RoleType,
    Group,
    Role,
    Bot,
    BotCreateDTO,
    Identity,
    UserCreateDTO,
    UserLdap,
    RoleCreationDTO,
    BotRoleCreateDTO,
)
from antarest.login.service import (
    LoginService,
    UserNotFoundError,
)

SADMIN = RequestParameters(
    user=JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
)

GADMIN = RequestParameters(
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


def assert_permission(
    test: Callable[[RequestParameters], Any],
    values: List[Tuple[RequestParameters, bool]],
    error=UserHasNotPermissionError,
):
    for params, res in values:
        if res:
            assert test(params)
        else:
            with pytest.raises(error):
                test(params)


def test_save_group():
    groups = Mock()
    groups.get_by_name.return_value = None
    groups.save.return_value = Group(id="group", name="group")

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )
    # Case 1 : Group name doesn't exist
    group = Group(id="group", name="group")
    assert_permission(
        test=lambda x: service.save_group(group, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )

    # Case 2 : Group name already exists
    groups.get_by_name.return_value = group
    assert_permission(
        test=lambda x: service.save_group(group, x),
        values=[(SADMIN, False), (GADMIN, False), (USER3, False)],
        error=HTTPException,
    )


def test_create_user():
    create = UserCreateDTO(name="hello", password="world")
    ldap = Mock()
    ldap.save.return_value = None

    users = Mock()
    users.save.return_value = User(id=3, name="hello")
    users.get_by_name.return_value = None

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=ldap,
        event_bus=Mock(),
    )

    service.create_user(create, param=SADMIN)
    users.save.assert_called_once_with(
        User(name="hello", password=Password("world"))
    )


def test_save_user():
    user = User(id=3)
    users = Mock()
    users.save.return_value = user

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.save_user(user, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_get_identity():
    user = User(id=1)
    ldap = UserLdap(id=2, name="Jane")
    bot = Bot(id=3, name="bot", owner=3, is_author=False)
    user_repo = Mock()
    ldap_repo = Mock(spec=LdapService)
    bot_repo = Mock()
    service = LoginService(
        user_repo=user_repo,
        bot_repo=bot_repo,
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=ldap_repo,
        event_bus=Mock(),
    )
    user_repo.get.return_value = user
    ldap_repo.get.return_value = None
    bot_repo.get.return_value = None
    assert service.get_identity(1) == user

    user_repo.get.return_value = None
    ldap_repo.get.return_value = ldap
    assert service.get_identity(2) == ldap

    ldap_repo.get.return_value = None
    assert service.get_identity(3) is None

    bot_repo.get.return_value = bot
    assert service.get_identity(3, True) == bot


def test_save_bot():
    bot_create = BotCreateDTO(
        name="bot",
        group="group",
        roles=[BotRoleCreateDTO(group="group", role=10)],
    )
    bots = Mock()
    bots.save.side_effect = lambda b: Bot(
        name=b.name,
        id=2,
        is_author=b.is_author,
        owner=b.owner,
    )
    bots.get_by_name_and_owner.return_value = None

    roles = Mock()
    roles.get.return_value = Role(
        identity=Identity(id=3), group=Group(id="group"), type=RoleType.WRITER
    )

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    res = service.save_bot(bot_create, USER3)
    assert res == Bot(name="bot", id=2, is_author=True, owner=3)


def test_save_bot_wrong_role():
    bot_create = BotCreateDTO(
        name="bot",
        group="group",
        roles=[BotRoleCreateDTO(group="group", role=40)],
    )
    bots = Mock()
    bots.save.side_effect = lambda b: b

    roles = Mock()
    roles.get.return_value = Role(
        identity=Identity(id=3), group=Group(id="group"), type=RoleType.READER
    )

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.save_bot(bot_create, x),
        values=[(USER3, False)],
    )


def test_save_role():
    role = RoleCreationDTO(
        type=RoleType.ADMIN, identity_id=0, group_id="group"
    )
    users = Mock()
    users.get.return_value = User(id=0, name="admin")
    groups = Mock()
    groups.get.return_value = Group(id="group", name="some group")
    roles = Mock()
    roles.save.return_value = role

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.save_role(role, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_get_group():
    group = Group(id="group", name="group")
    groups = Mock()
    groups.get.return_value = group

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_group("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
    )


def test_get_group_info():
    groups = Mock()
    group = Group(id="group", name="group")
    groups.get.return_value = group

    users = Mock()
    user = User(id=3, name="John")
    users.get.return_value = user

    ldap = Mock(spec=LdapService)
    ldap.get.return_value = UserLdap(id=4, name="Jane")

    roles = Mock()
    roles.get_all_by_group.return_value = [
        Role(group=group, identity=user, type=RoleType.RUNNER)
    ]
    roles.get_all_by_user.return_value = [
        Role(group=group, identity=user, type=RoleType.RUNNER)
    ]

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=roles,
        ldap=ldap,
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_group_info("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_get_user():
    user = User(id=3)
    users = Mock()
    users.get.return_value = user

    ldap = Mock()
    ldap.get.return_value = None

    role = Role(type=RoleType.READER, identity=user, group=Group(id="group"))
    roles = Mock()
    roles.get_all_by_user.return_value = [role]

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=ldap,
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_user(3, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
        error=UserNotFoundError,
    )


def test_get_user_info():
    users = Mock()
    user_ok = User(id=3, name="user")
    user_nok = User(id=2, name="user")

    ldap = Mock()
    ldap.get.return_value = None

    roles = Mock()
    group_ok = Group(id="group", name="group")
    group_nok = Group(id="other_group", name="group")

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=ldap,
        event_bus=Mock(),
    )

    user_id = 3
    # When GADMIN ok, USER3 is himself
    users.get.return_value = user_ok
    roles.get_all_by_user.return_value = [
        Role(type=RoleType.ADMIN, group=group_ok, identity=user_ok)
    ]
    assert_permission(
        test=lambda x: service.get_user_info(user_id, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
    )

    # When GADMIN not ok, USER3 is not himself
    users.get.return_value = user_nok
    roles.get_all_by_user.return_value = [
        Role(type=RoleType.ADMIN, group=group_nok, identity=user_nok)
    ]
    assert_permission(
        test=lambda x: service.get_user_info(user_id, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
        error=UserNotFoundError,
    )


def test_get_bot():
    bots = Mock()
    bots.get.return_value = Bot(owner=3)

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_bot(3, x),
        values=[(SADMIN, True), (USER3, True), (GADMIN, False)],
        error=UserHasNotPermissionError,
    )


def test_get_bot_info():
    bots = Mock()
    bot = Bot(id=4, name="bot", owner=3, is_author=False)
    bots.get.return_value = bot

    roles = Mock()
    group = Group(id="group", name="group")

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    bot_id = 3
    # When USER3 is himself
    bots.get.return_value = bot
    roles.get_all_by_user.return_value = [
        Role(type=RoleType.ADMIN, group=group, identity=bot)
    ]
    assert_permission(
        test=lambda x: service.get_bot_info(bot_id, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_authentication_wrong_user():
    users = Mock()
    users.get_by_name.return_value = None

    ldap = Mock()
    ldap.login.return_value = None
    ldap.get_by_name.return_value = None

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=ldap,
        event_bus=Mock(),
    )
    assert not service.authenticate("dupond", "pwd")
    users.get_by_name.assert_called_once_with("dupond")


def test_authenticate():
    users = Mock()
    users.get_by_name.return_value = User(id=0, password=Password("pwd"))
    users.get.return_value = User(id=0, name="linus")

    ldap = Mock()
    ldap.login.return_value = None
    ldap.get.return_value = None

    roles = Mock()
    roles.get_all_by_user.return_value = [
        Role(type=RoleType.READER, group=Group(id="group", name="group"))
    ]

    exp = JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="group", name="group", role=RoleType.READER)],
    )

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=ldap,
        event_bus=Mock(),
    )
    assert exp == service.authenticate("dupond", "pwd")

    users.get_by_name.assert_called_once_with("dupond")
    roles.get_all_by_user.assert_called_once_with(0)


def test_authentication_ldap_user():
    users = Mock()
    users.get_by_name.return_value = None

    roles = Mock()
    roles.get_all_by_user.return_value = []

    ldap = Mock()
    user = UserLdap(id=10, name="ExtUser")
    ldap.login.return_value = user
    ldap.get.return_value = user

    exp = JWTUser(
        id=10,
        impersonator=10,
        type="users_ldap",
    )

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=ldap,
        event_bus=Mock(),
    )
    assert exp == service.authenticate("dupond", "pwd")
    ldap.get.assert_called_once_with(10)


def test_get_all_groups():
    group = Group(id="my-group", name="my-group")
    groups = Mock()
    groups.get_all.return_value = [group]

    user = User(id=3, name="name")
    role = Role(group=group, identity=user)
    roles = Mock()
    roles.get_all_by_user.return_value = [role]

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_groups(x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
    )


def test_get_all_users():
    users = Mock()
    users.get_all.return_value = [User(id=0, name="alice")]

    ldap = Mock()
    ldap.get_all.return_value = []

    user = User(id=3, name="user")
    role_gadmin_ok = Role(
        group=Group(id="group"), type=RoleType.ADMIN, identity=user
    )

    role_repo = Mock()
    role_repo.get_all_by_user.return_value = [role_gadmin_ok]
    role_repo.get_all_by_group.return_value = [role_gadmin_ok]

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=role_repo,
        ldap=ldap,
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_users(x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
    )


def test_get_all_bots():
    bots = Mock()
    bots.get_all.return_value = [Bot(id=0, name="alice")]

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_bots(x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )


def test_get_all_bots_by_owner():
    bots = Mock()
    bots.get_all_by_owner.return_value = [Bot(id=0, name="alice")]

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_bots_by_owner(3, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_get_all_roles_in_group():
    roles = Mock()
    roles.get_all_by_group.return_value = [Role()]

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_roles_in_group("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_delete_group():
    groups = Mock()
    groups.delete.return_value = Group()

    roles = Mock()
    roles.get_all_by_group.return_value = []

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.delete_group("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_delete_user():
    users = Mock()
    users.delete.return_value = User()

    bots = Mock()
    bots.get_all_by_owner.return_value = [Bot(id=4, owner=3)]
    bots.get.return_value = Bot(id=4, owner=3)

    roles = Mock()
    roles.get_all_by_user.return_value = []

    service = LoginService(
        user_repo=users,
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.delete_user(3, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )

    users.delete.assert_called_with(3)
    bots.delete.assert_called_with(4)


def test_delete_bot():
    bots = Mock()
    bots.delete.return_value = Bot()
    bots.get.return_value = Bot(id=4, owner=3)

    roles = Mock()
    roles.get_all_by_user.return_value = []

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.delete_bot(3, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_delete_role():
    roles = Mock()
    roles.delete.return_value = Role()

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.delete_role(3, "group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_delete_all_roles():
    roles = Mock()
    user = User(id=3, name="user")
    role_gadmin_ok = Role(
        group=Group(id="group"), type=RoleType.READER, identity=user
    )
    role_gadmin_nok = Role(
        group=Group(id="other-group"), type=RoleType.READER, identity=user
    )

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=roles,
        ldap=Mock(),
        event_bus=Mock(),
    )

    user_id = 3
    # GADMIN OK
    roles.get_all_by_user.return_value = [role_gadmin_ok]
    assert_permission(
        test=lambda x: service.delete_all_roles_from_user(user_id, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )
    # GADMIN NOK
    roles.get_all_by_user.return_value = [role_gadmin_nok]
    assert_permission(
        test=lambda x: service.delete_all_roles_from_user(user_id, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )
