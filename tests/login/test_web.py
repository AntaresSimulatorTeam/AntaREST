import base64
import json
from pathlib import Path
from typing import Any, Dict, Tuple
from unittest.mock import Mock

import pytest
from flask import Flask
from flask_jwt_extended import create_access_token

from antarest.common.config import Config
from antarest.login.main import build_login
from antarest.login.model import User, Role, Password, Group


def create_client(service: Mock) -> Any:

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]

    build_login(
        app,
        service=service,
        config=Config({"main": {"res": Path(), "local": False}}),
        db_session=Mock(),
    )
    return app.test_client()


def get_access_token(role: str = Role.USER) -> Dict[str, str]:
    if role == Role.USER:
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxMzQ2NzA3NSwianRpIjoiMTZlZDc3NmMtNmNlMS00MDdhLWFkMmItMzFiN2M0NjkyOTA5IiwibmJmIjoxNjEzNDY3MDc1LCJ0eXBlIjoiYWNjZXNzIiwic3ViIjp7ImlkIjoxLCJuYW1lIjoidXNlciIsInJvbGUiOiJVU0VSIn0sImNzcmYiOiI0ODIzYTlmYi1mNzJiLTQxZTAtODk1Mi1lYWU3MjlkNGUxZjQiLCJleHAiOjk5OTk5OTk5OTl9.QIcMKIEm_rE_0KrNgWMKE9ykAU9eHcbGckGFE8hhTk0"
    elif role == Role.ADMIN:
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxMzQ2NzA3NSwianRpIjoiMTZlZDc3NmMtNmNlMS00MDdhLWFkMmItMzFiN2M0NjkyOTA5IiwibmJmIjoxNjEzNDY3MDc1LCJ0eXBlIjoiYWNjZXNzIiwic3ViIjp7ImlkIjowLCJuYW1lIjoiYWRtaW4iLCJyb2xlIjoiQURNSU4ifSwiY3NyZiI6IjQ4MjNhOWZiLWY3MmItNDFlMC04OTUyLWVhZTcyOWQ0ZTFmNCIsImV4cCI6OTk5OTk5OTk5OX0.hvvGLnqbRzbuGyCmjuecX5-puMYDDOwsFXZHiUMJyFk"
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = User(id=0, name="admin")

    client = create_client(service)
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

    client = create_client(service)
    res = client.post(
        "/login", json={"username": "admin", "password": "admin"}
    )

    assert res.status_code == 401


@pytest.mark.unit_test
def test_refresh() -> None:
    service = Mock()
    service.get_user.return_value = User(id=0, name="admin", role=Role.USER)

    client = create_client(service)
    res = client.post("/refresh", headers=get_access_token())

    assert res.status_code == 200
    data = res.json

    meta, b64, sign = data["access_token"].split(".")
    identity = json.loads(base64.b64decode(b64))["sub"]
    assert Role.USER == identity["role"]


@pytest.mark.unit_test
def test_user_fail() -> None:
    service = Mock()
    service.get_all_users.return_value = [
        User(id=1, name="user", role=Role.USER)
    ]

    client = create_client(service)
    res = client.get("/users", headers=get_access_token())
    assert res.status_code == 403


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all_users.return_value = [
        User(id=1, name="user", role=Role.USER)
    ]

    client = create_client(service)
    res = client.get("/users", headers=get_access_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == [User(id=1, name="user", role=Role.USER).to_dict()]


@pytest.mark.unit_test
def test_user_id() -> None:
    service = Mock()
    service.get_user.return_value = User(id=1, name="user", role=Role.USER)

    client = create_client(service)
    res = client.get("/users/1", headers=get_access_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == User(id=1, name="user", role=Role.USER).to_dict()


@pytest.mark.unit_test
def test_user_create() -> None:
    user = User(id=1, name="a", role=Role.USER, password=Password("b"))
    service = Mock()
    service.save_user.return_value = user

    client = create_client(service)
    res = client.post(
        "/users",
        headers=get_access_token(Role.ADMIN),
        json={"name": "a", "password": "b", "role": "USER"},
    )

    assert res.status_code == 200
    assert res.json == user.to_dict()


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    client = create_client(service)
    res = client.delete("/users/0", headers=get_access_token(Role.ADMIN))

    assert res.status_code == 200
    service.delete_user.assert_called_once_with(0)


@pytest.mark.unit_test
def test_groups_fail() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id=1, name="group")]

    client = create_client(service)
    res = client.get("/groups", headers=get_access_token())
    assert res.status_code == 403


@pytest.mark.unit_test
def test_group() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id=1, name="group")]

    client = create_client(service)
    res = client.get("/groups", headers=get_access_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == [Group(id=1, name="group").to_dict()]


@pytest.mark.unit_test
def test_group_id() -> None:
    service = Mock()
    service.get_group.return_value = Group(id=1, name="group")

    client = create_client(service)
    res = client.get("/groups/1", headers=get_access_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == Group(id=1, name="group").to_dict()


@pytest.mark.unit_test
def test_group_create() -> None:
    group = Group(id=1, name="group")
    service = Mock()
    service.save_group.return_value = group

    client = create_client(service)
    res = client.post(
        "/groups",
        headers=get_access_token(Role.ADMIN),
        json={"name": "group"},
    )

    assert res.status_code == 200
    assert res.json == group.to_dict()


@pytest.mark.unit_test
def test_group_delete() -> None:
    service = Mock()

    client = create_client(service)
    res = client.delete("/groups/0", headers=get_access_token(Role.ADMIN))

    assert res.status_code == 200
    service.delete_group.assert_called_once_with(0)
