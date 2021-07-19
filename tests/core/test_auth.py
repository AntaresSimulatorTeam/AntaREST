from unittest.mock import Mock

from fastapi import FastAPI

from antarest.login.auth import Auth
from antarest.core.config import Config, SecurityConfig
from antarest.login.model import RoleType


def create_app() -> FastAPI:
    app = FastAPI(title=__name__)
    return app


def build(security_disabled: bool = False, admin: bool = False) -> Auth:
    get_identity = Mock()
    get_identity.return_value = {
        "id": 0,
        "impersonator": 0,
        "type": "users",
        "groups": [
            {
                "id": "admin" if admin else "group",
                "name": "group",
                "role": RoleType.ADMIN.to_dict(),
            }
        ],
    }

    config = Config(security=SecurityConfig(disabled=security_disabled))

    return Auth(config=config, verify=Mock(), get_identity=get_identity)


def endpoint():
    return "Hello", 200


def test_local() -> None:
    auth = build(security_disabled=True)

    assert auth.get_current_user() is not None


# def test_admin_matched() -> None:
#     auth = build(security_disabled=False, admin=True)
#
#
#     with create_app().app_context():
#         res, code = auth.protected(admin=True)(endpoint)()
#     assert code == 200
#
#
# def test_fail() -> None:
#     auth = build(security_disabled=False)
#
#     with create_app().app_context():
#         res, code = auth.protected(admin=True)(endpoint)()
#     assert code == 403
#
#
# def test_no_filter() -> None:
#     auth = build(security_disabled=False)
#
#     with create_app().app_context():
#         res, code = auth.protected()(endpoint)()
#     assert code == 200
