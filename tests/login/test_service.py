from typing import Any, Callable, List, Tuple
from unittest.mock import Mock

import pytest

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
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
)
from antarest.login.service import (
    LoginService,
    GroupNotFoundError,
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
    groups.save.return_value = Group(id="group", name="group")

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    group = Group(id="group", name="group")
    assert_permission(
        test=lambda x: service.save_group(group, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
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


def test_create_user_ldap():
    create = UserCreateDTO(name="hello", password="world")
    ldap = Mock()
    ldap.save.return_value = UserLdap(name="hello")

    users = Mock()
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
    users.save.assert_not_called()


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


def test_save_bot():
    bot_create = BotCreateDTO(name="bot", group="group", role=RoleType.READER)
    bots = Mock()
    bots.save.side_effect = lambda b: b

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
    assert res == Bot(name="bot", is_author=True, owner=3)


def test_save_bot_wrong_role():
    bot_create = BotCreateDTO(name="bot", group="group", role=RoleType.ADMIN)
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
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
        error=GroupNotFoundError,
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


def test_authentication_wrong_user():
    users = Mock()
    users.get_by_name.return_value = None

    ldap = Mock()
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
    ldap.get_by_name.return_value = None
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


def test_get_all_groups():
    group = Group(id="my-group")
    groups = Mock()
    groups.get_all.return_value = [group]

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_groups(x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )


def test_get_all_users():
    users = Mock()
    users.get_all.return_value = [User(id=0, name="alice")]

    ldap = Mock()
    ldap.get_all.return_value = []

    service = LoginService(
        user_repo=users,
        bot_repo=Mock(),
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=ldap,
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.get_all_users(x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
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

    service = LoginService(
        user_repo=Mock(),
        bot_repo=Mock(),
        group_repo=groups,
        role_repo=Mock(),
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

    service = LoginService(
        user_repo=users,
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=Mock(),
        ldap=Mock(),
        event_bus=Mock(),
    )

    assert_permission(
        test=lambda x: service.delete_user(3, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )

    users.delete.assert_called_with(3)
    bots.delete.assert_called_with(4)


def test_delete_bot():
    bots = Mock()
    bots.delete.return_value = Bot()
    bots.get.return_value = Bot(id=4, owner=3)

    service = LoginService(
        user_repo=Mock(),
        bot_repo=bots,
        group_repo=Mock(),
        role_repo=Mock(),
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
