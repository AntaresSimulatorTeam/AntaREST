from unittest.mock import Mock

from antarest.common.jwt import JWTRole, JWTUser, JWTGroup
from antarest.login.model import User, Password, Role, Group
from antarest.login.service import LoginService


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
        Role(type=JWTRole.READER, group=Group(id="group", name="group"))
    ]

    exp = JWTUser(
        id=0,
        name="linus",
        groups=[JWTGroup(id="group", name="group", role=JWTRole.READER)],
    )

    service = LoginService(
        user_repo=users, group_repo=Mock(), role_repo=roles, event_bus=Mock()
    )
    assert exp == service.authenticate("dupond", "pwd")

    users.get_by_name.assert_called_once_with("dupond")
    roles.get_all_by_user.assert_called_once_with(0)
