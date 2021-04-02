import base64
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from flask import Flask
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from antarest.common.config import Config, SecurityConfig
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import RequestParameters
from antarest.login.main import build_login
from antarest.login.model import User, RoleType, Password, Group, Role

PARAMS = RequestParameters(
    user=JWTUser(
        id=0,
        name="admin",
        groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
    )
)


def create_app(service: Mock, auth_disabled=False) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]

    build_login(
        app,
        service=service,
        config=Config(
            resources_path=Path(),
            security=SecurityConfig(disabled=auth_disabled),
        ),
        db_session=Mock(),
    )
    return app


class TokenType:
    REFRESH: str = "REFRESH"
    ACCESS: str = "ACCESS"


def create_auth_token(
    app: Flask,
    expires_delta: Any = timedelta(days=2),
    type: TokenType = TokenType.ACCESS,
) -> Dict[str, str]:
    create_token = (
        create_access_token
        if type == TokenType.ACCESS
        else create_refresh_token
    )
    with app.app_context():
        token = create_token(
            expires_delta=expires_delta,
            identity=JWTUser(
                id=0,
                name="admin",
                groups=[
                    JWTGroup(id="group", name="group", role=RoleType.ADMIN)
                ],
            ).to_dict(),
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit_test
def test_auth_needed() -> None:
    service = Mock()

    app = create_app(service)
    client = app.test_client()
    res = client.get("/auth", headers=create_auth_token(app))
    assert res.status_code == 200

    res = client.get("/auth")
    assert res.status_code == 401

    app = create_app(service, True)
    client = app.test_client()
    res = client.get("/auth")
    assert res.status_code == 200


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/login", json={"username": "admin", "password": "admin"}
    )

    assert res.status_code == 200
    assert res.json["access_token"]

    service.authenticate.assert_called_once_with("admin", "admin")


@pytest.mark.unit_test
def test_auth_fail() -> None:
    service = Mock()
    service.authenticate.return_value = None

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/login", json={"username": "admin", "password": "admin"}
    )

    assert res.status_code == 401


@pytest.mark.unit_test
def test_expiration() -> None:
    service = Mock()
    service.get_user.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/users",
        headers=create_auth_token(app, expires_delta=timedelta(days=-1)),
    )

    assert res.status_code == 401
    data = res.json
    assert data["msg"] == "Token has expired"


@pytest.mark.unit_test
def test_refresh() -> None:
    service = Mock()
    service.get_jwt.return_value = User(id=0, name="admin")

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/refresh",
        headers=create_auth_token(app, type=TokenType.REFRESH),
    )

    assert res.status_code == 200
    data = res.json
    meta, b64, sign = str(data["access_token"]).split(".")

    data = b64 + "==="  # fix padding issue
    identity = json.loads(base64.b64decode(data))["sub"]


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all_users.return_value = [User(id=1, name="user")]

    app = create_app(service)
    client = app.test_client()
    res = client.get("/users", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json == [User(id=1, name="user").to_dict()]


@pytest.mark.unit_test
def test_user_id() -> None:
    service = Mock()
    service.get_user.return_value = User(id=1, name="user")

    app = create_app(service)
    client = app.test_client()
    res = client.get("/users/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json == User(id=1, name="user").to_dict()


@pytest.mark.unit_test
def test_user_create() -> None:
    user = User(name="a", password=Password("b"))
    user_id = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.save_user.return_value = user_id

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/users",
        headers=create_auth_token(app),
        json={
            "name": "a",
            "password": "b",
        },
    )

    assert res.status_code == 200
    service.save_user.assert_called_once_with(user, PARAMS)
    assert res.json == user_id.to_dict()


@pytest.mark.unit_test
def test_user_save() -> None:
    user = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.save_user.return_value = user

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/users/0",
        headers=create_auth_token(app),
        json=user.to_dict(),
    )

    assert res.status_code == 200
    service.save_user.assert_called_once_with(user, PARAMS)
    assert res.json == user.to_dict()


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = app.test_client()
    res = client.delete("/users/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_user.assert_called_once_with(0, PARAMS)


@pytest.mark.unit_test
def test_group() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id="my-group", name="group")]

    app = create_app(service)
    client = app.test_client()
    res = client.get("/groups", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json == [Group(id="my-group", name="group").to_dict()]


@pytest.mark.unit_test
def test_group_id() -> None:
    service = Mock()
    service.get_group.return_value = Group(id="my-group", name="group")

    app = create_app(service)
    client = app.test_client()
    res = client.get("/groups/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json == Group(id="my-group", name="group").to_dict()


@pytest.mark.unit_test
def test_group_create() -> None:
    group = Group(id="my-group", name="group")
    service = Mock()
    service.save_group.return_value = group

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/groups",
        headers=create_auth_token(app),
        json={"name": "group"},
    )

    assert res.status_code == 200
    assert res.json == group.to_dict()


@pytest.mark.unit_test
def test_group_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = app.test_client()
    print(create_auth_token(app))
    res = client.delete("/groups/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_group.assert_called_once_with(0, PARAMS)


@pytest.mark.unit_test
def test_role() -> None:
    role = Role(
        user=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.get_all_roles_in_group.return_value = [role]

    app = create_app(service)
    client = app.test_client()
    res = client.get("/roles/group/g", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json == [role.to_dict()]


@pytest.mark.unit_test
def test_role_create() -> None:
    role = Role(
        user=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.save_role.return_value = role

    app = create_app(service)
    client = app.test_client()
    res = client.post(
        "/roles",
        headers=create_auth_token(app),
        json=role.to_dict(),
    )

    assert res.status_code == 200
    assert res.json == role.to_dict()


@pytest.mark.unit_test
def test_role_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = app.test_client()
    res = client.delete("/roles/group/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_role.assert_called_once_with(0, "group", PARAMS)
