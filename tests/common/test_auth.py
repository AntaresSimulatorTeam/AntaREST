from unittest.mock import Mock

from antarest.common.auth import Auth
from antarest.common.config import Config
from antarest.login.model import Role


def build(local: bool = False, role: str = Role.USER) -> Auth:
    get_identity = Mock()
    get_identity.return_value = {"role": role}

    config = Config({"main": {"local": local}})

    return Auth(config=config, verify=Mock(), get_identity=get_identity)


def test_local() -> None:
    auth = build(local=True)

    res, code = auth.protected()(lambda: ("Hello", 200))()
    assert code == 200


def test_role_matched() -> None:
    auth = build(local=False, role=Role.ADMIN)

    res, code = auth.protected(roles=[Role.ADMIN])(lambda: ("Hello", 200))()
    assert code == 200


def test_fail() -> None:
    auth = build(local=False)

    res, code = auth.protected(roles=[Role.ADMIN])(lambda: ("Hello", 200))()
    assert code == 403


def test_no_filter() -> None:
    auth = build(local=False)

    res, code = auth.protected()(lambda: ("Hello", 200))()
    assert code == 200
