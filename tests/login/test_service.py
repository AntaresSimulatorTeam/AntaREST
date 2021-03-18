from unittest.mock import Mock

from antarest.login.model import User, Password
from antarest.login.service import LoginService


def test_authenticate():
    repo = Mock()
    repo.get_by_name.return_value = User(password="pwd")

    service = LoginService(user_repo=repo, group_repo=Mock())
    assert service.authenticate("dupond", "pwd")
    repo.get_by_name.assert_called_once_with("dupond")


def test_authentication_wrong_user():
    repo = Mock()
    repo.get_by_name.return_value = None

    service = LoginService(user_repo=repo, group_repo=Mock(), event_bus=Mock())
    assert not service.authenticate("dupond", "pwd")
    repo.get_by_name.assert_called_once_with("dupond")


def test_authenticate():
    repo = Mock()
    repo.get_by_name.return_value = User(password=Password("pwd"))

    service = LoginService(user_repo=repo, group_repo=Mock(), event_bus=Mock())
    assert not service.authenticate("dupond", "wrong")
    repo.get_by_name.assert_called_once_with("dupond")


def test_identify():
    user = User(id=0, name="user", password=Password("pwd"))
    repo = Mock()
    repo.get.return_value = user

    service = LoginService(user_repo=repo, group_repo=Mock(), event_bus=Mock())
    assert user == service.identify({"identity": 0})
