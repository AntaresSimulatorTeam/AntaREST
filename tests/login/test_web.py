import base64
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Union
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi_jwt_auth import AuthJWT
from starlette.testclient import TestClient

from antarest.common.config import Config, SecurityConfig
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import RequestParameters
from antarest.login.main import build_login
from antarest.login.model import (
    User,
    RoleType,
    Password,
    Group,
    Role,
    BotCreateDTO,
    Bot,
    UserCreateDTO,
    IdentityDTO,
    BotRoleCreateDTO,
)
from antarest.main import JwtSettings

PARAMS = RequestParameters(
    user=JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
    )
)


def create_app(service: Mock, auth_disabled=False) -> FastAPI:
    app = FastAPI(title=__name__)

    @AuthJWT.load_config
    def get_config():
        return JwtSettings(
            authjwt_secret_key="super-secret",
            authjwt_token_location=("headers", "cookies"),
        )

    build_login(
        app,
        service=service,
        config=Config(
            resources_path=Path(),
            security=SecurityConfig(disabled=auth_disabled),
        ),
    )
    return app


class TokenType:
    REFRESH: str = "REFRESH"
    ACCESS: str = "ACCESS"


def create_auth_token(
    app: FastAPI,
    expires_delta: Union[int, timedelta] = timedelta(days=2),
    type: TokenType = TokenType.ACCESS,
) -> Dict[str, str]:
    jwt_manager = AuthJWT()
    create_token = (
        jwt_manager.create_access_token
        if type == TokenType.ACCESS
        else jwt_manager.create_refresh_token
    )
    token = create_token(
        expires_time=expires_delta,
        subject=json.dumps(
            JWTUser(
                id=0,
                impersonator=0,
                type="users",
                groups=[
                    JWTGroup(id="group", name="group", role=RoleType.ADMIN)
                ],
            ).to_dict(),
        ),
    )
    return {
        "Authorization": f"Bearer {token if isinstance(token, str) else token.decode()}"
    }


@pytest.mark.unit_test
def test_auth_needed() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/auth", headers=create_auth_token(app))
    assert res.status_code == 200

    res = client.get("/auth")
    assert res.status_code == 401

    app = create_app(service, True)
    client = TestClient(app)
    res = client.get("/auth")
    assert res.status_code == 200


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/login", json={"username": "admin", "password": "admin"}
    )

    assert res.status_code == 200
    assert res.json()["access_token"]

    service.authenticate.assert_called_once_with("admin", "admin")


@pytest.mark.unit_test
def test_auth_fail() -> None:
    service = Mock()
    service.authenticate.return_value = None

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/login", json={"username": "admin", "password": "admin"}
    )

    assert res.status_code == 401


@pytest.mark.unit_test
def test_expiration() -> None:
    service = Mock()
    service.get_user.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get(
        "/users",
        headers=create_auth_token(app, expires_delta=timedelta(days=-1)),
    )

    assert res.status_code == 401
    data = res.json()
    assert data["detail"] == "Signature has expired"


@pytest.mark.unit_test
def test_refresh() -> None:
    service = Mock()
    service.get_jwt.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/refresh",
        headers=create_auth_token(app, type=TokenType.REFRESH),
    )

    assert res.status_code == 200
    data = res.json()
    meta, b64, sign = str(data["access_token"]).split(".")

    data = b64 + "==="  # fix padding issue
    identity = json.loads(base64.b64decode(data))["sub"]


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all_users.return_value = [User(id=1, name="user")]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/users", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [User(id=1, name="user").to_dict()]


@pytest.mark.unit_test
def test_user_id() -> None:
    service = Mock()
    service.get_user.return_value = User(id=1, name="user")

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/users/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == User(id=1, name="user").to_dict()


@pytest.mark.unit_test
def test_user_id_with_details() -> None:
    service = Mock()
    service.get_user_info.return_value = IdentityDTO(
        id=1, name="user", roles=[]
    )

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/users/1?details=true", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == IdentityDTO(id=1, name="user", roles=[]).to_dict()


@pytest.mark.unit_test
def test_user_create() -> None:
    user = UserCreateDTO(name="a", password="b")
    user_id = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.create_user.return_value = user_id

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/users",
        headers=create_auth_token(app),
        json=user.dict(),
    )

    assert res.status_code == 200
    service.create_user.assert_called_once_with(user, PARAMS)
    assert res.json() == user_id.to_dict()


@pytest.mark.unit_test
def test_user_save() -> None:
    user = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.save_user.return_value = user

    app = create_app(service)
    client = TestClient(app)
    res = client.put(
        "/users/0",
        headers=create_auth_token(app),
        json=user.to_dict(),
    )

    assert res.status_code == 200
    service.save_user.assert_called_once_with(user, PARAMS)
    assert res.json() == user.to_dict()


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/users/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_user.assert_called_once_with(0, PARAMS)


@pytest.mark.unit_test
def test_group() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id="my-group", name="group")]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/groups", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [Group(id="my-group", name="group").to_dict()]


@pytest.mark.unit_test
def test_group_id() -> None:
    service = Mock()
    service.get_group.return_value = Group(id="my-group", name="group")

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/groups/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == Group(id="my-group", name="group").to_dict()


@pytest.mark.unit_test
def test_group_create() -> None:
    group = Group(id="my-group", name="group")
    service = Mock()
    service.save_group.return_value = group

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/groups",
        headers=create_auth_token(app),
        json={"name": "group"},
    )

    assert res.status_code == 200
    assert res.json() == group.to_dict()


@pytest.mark.unit_test
def test_group_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    print(create_auth_token(app))
    res = client.delete("/groups/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_group.assert_called_once_with("0", PARAMS)


@pytest.mark.unit_test
def test_role() -> None:
    role = Role(
        identity=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.get_all_roles_in_group.return_value = [role]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/roles/group/g", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [role.to_dict()]


@pytest.mark.unit_test
def test_role_create() -> None:
    role = Role(
        identity=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.save_role.return_value = role

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/roles",
        headers=create_auth_token(app),
        json={"type": RoleType.ADMIN.value, "identity_id": 0, "group_id": "g"},
    )

    assert res.status_code == 200
    assert res.json() == role.to_dict()


@pytest.mark.unit_test
def test_role_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/roles/group/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_role.assert_called_once_with(0, "group", PARAMS)


@pytest.mark.unit_test
def test_roles_delete_by_user() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/users/roles/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_all_roles_from_user.assert_called_once_with(0, PARAMS)


@pytest.mark.unit_test
def test_bot_create() -> None:
    bot = Bot(id=2, owner=3, name="bot", is_author=False)
    create = BotCreateDTO(
        name="bot",
        group="group",
        roles=[BotRoleCreateDTO(group="group", role=40)],
    )

    service = Mock()
    service.save_bot.return_value = bot
    service.get_group.return_value = Group(id="group", name="group")

    print(create.json())
    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/bots", headers=create_auth_token(app), json=create.dict()
    )

    assert res.status_code == 200
    assert len(res.json().split(".")) == 3


@pytest.mark.unit_test
def test_bot() -> None:
    bot = Bot(id=0, owner=4, is_author=False)
    service = Mock()
    service.get_bot.return_value = bot

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/bots/0", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == bot.to_dict()


@pytest.mark.unit_test
def test_all_bots() -> None:
    bots = [Bot(id=0, owner=4, is_author=False)]
    service = Mock()
    service.get_all_bots.return_value = bots
    service.get_all_bots_by_owner.return_value = bots

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/bots", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [b.to_dict() for b in bots]

    res = client.get("/bots?owner=4", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [b.to_dict() for b in bots]

    service.get_all_bots.assert_called_once()
    service.get_all_bots_by_owner.assert_called_once()


@pytest.mark.unit_test
def test_bot_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/bots/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_bot.assert_called_once_with(0, PARAMS)
