from typing import Any, Callable, List, Tuple
from unittest.mock import Mock

import pytest

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.model import User, Password, RoleType, Group, Role
from antarest.login.service import (
    LoginService,
    GroupNotFoundError,
    UserNotFoundError,
)

SADMIN = RequestParameters(
    user=JWTUser(
        id=0,
        name="admin",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
)

GADMIN = RequestParameters(
    user=JWTUser(
        id=1,
        name="alice",
        groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
    )
)

USER3 = RequestParameters(
    user=JWTUser(
        id=3,
        name="bob",
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
        user_repo=Mock(), group_repo=groups, role_repo=Mock(), event_bus=Mock()
    )

    group = Group(id="group", name="group")
    assert_permission(
        test=lambda x: service.save_group(group, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_save_user():
    user = User(id=3)
    users = Mock()
    users.save.return_value = user

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=Mock(), event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.save_user(user, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_save_role():
    role = Role(type=RoleType.ADMIN, user=User(id=0), group=Group(id="group"))
    roles = Mock()
    roles.save.return_value = role

    service = LoginService(
        user_repo=Mock(), group_repo=Mock(), role_repo=roles, event_bus=Mock()
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
        user_repo=Mock(), group_repo=groups, role_repo=Mock(), event_bus=Mock()
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

    role = Role(type=RoleType.READER, user=user, group=Group(id="group"))
    roles = Mock()
    roles.get_all_by_user.return_value = [role]

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=roles, event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.get_user(3, x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, True)],
        error=UserNotFoundError,
    )


def test_authentication_wrong_user():
    users = Mock()
    users.get_by_name.return_value = None

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=Mock(), event_bus=Mock()
    )
    assert not service.authenticate("dupond", "pwd")
    users.get_by_name.assert_called_once_with("dupond")


def test_authenticate():
    users = Mock()
    users.get_by_name.return_value = User(id=0, password=Password("pwd"))
    users.get.return_value = User(id=0, name="linus")

    roles = Mock()
    roles.get_all_by_user.return_value = [
        Role(type=RoleType.READER, group=Group(id="group", name="group"))
    ]

    exp = JWTUser(
        id=0,
        name="linus",
        groups=[JWTGroup(id="group", name="group", role=RoleType.READER)],
    )

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=roles, event_bus=Mock()
    )
    assert exp == service.authenticate("dupond", "pwd")

    users.get_by_name.assert_called_once_with("dupond")
    roles.get_all_by_user.assert_called_once_with(0)


def test_get_all_groups():
    group = Group(id="my-group")
    groups = Mock()
    groups.get_all.return_value = [group]

    service = LoginService(
        user_repo=Mock(), group_repo=groups, role_repo=Mock(), event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.get_all_groups(x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )


def test_get_all_users():
    users = Mock()
    users.get_all.return_value = [User(id=0, name="alice")]

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=Mock(), event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.get_all_users(x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, False)],
    )


def test_get_all_roles_in_group():
    roles = Mock()
    roles.get_all_by_group.return_value = [Role()]

    service = LoginService(
        user_repo=Mock(), group_repo=Mock(), role_repo=roles, event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.get_all_roles_in_group("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_delete_group():
    groups = Mock()
    groups.delete.return_value = Group()

    service = LoginService(
        user_repo=Mock(), group_repo=groups, role_repo=Mock(), event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.delete_group("group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )


def test_delete_user():
    users = Mock()
    users.delete.return_value = User()

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=Mock(), event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.delete_user(3, x),
        values=[(SADMIN, True), (GADMIN, False), (USER3, True)],
    )


def test_delete_role():
    roles = Mock()
    roles.delete.return_value = Role()

    service = LoginService(
        user_repo=Mock(), group_repo=Mock(), role_repo=roles, event_bus=Mock()
    )

    assert_permission(
        test=lambda x: service.delete_role(3, "group", x),
        values=[(SADMIN, True), (GADMIN, True), (USER3, False)],
    )
