from unittest.mock import Mock

from flask import Flask

from antarest.common.auth import Auth
from antarest.common.config import Config
from antarest.login.model import Role, User


def create_app() -> Flask:
    app = Flask(__name__)
    return app


def build(security_disabled: bool = False, role: str = Role.USER) -> Auth:
    get_identity = Mock()
    get_identity.return_value = {id: 0, "name": "admin", "role": role}

    config = Config({"security": {"disabled": security_disabled}})

    return Auth(config=config, verify=Mock(), get_identity=get_identity)


def endpoint():
    return "Hello", 200


def test_local() -> None:
    auth = build(security_disabled=True)

    with create_app().app_context():
        res, code = auth.protected()(endpoint)()
    assert code == 200


def test_role_matched() -> None:
    auth = build(security_disabled=False, role=Role.ADMIN)

    with create_app().app_context():
        res, code = auth.protected(roles=[Role.ADMIN])(endpoint)()
    assert code == 200


def test_fail() -> None:
    auth = build(security_disabled=False)

    with create_app().app_context():
        res, code = auth.protected(roles=[Role.ADMIN])(endpoint)()
    assert code == 403


def test_no_filter() -> None:
    auth = build(security_disabled=False)

    with create_app().app_context():
        res, code = auth.protected()(endpoint)()
    assert code == 200
