from typing import Any, Dict, Tuple
from unittest.mock import Mock

import pytest
from flask import Flask

from antarest.login.main import build_login
from antarest.login.model import User, Role


def create_client(
    service: Mock, admin: bool = False
) -> Tuple[Any, Dict[str, str]]:
    service.authenticate.return_value = User(
        id=0, name="user", role=Role.ADMIN if admin else Role.USER
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"

    build_login(app, service=service)
    client = app.test_client()

    res = client.post("/auth", json={"username": "admin", "password": "admin"})
    token = res.json["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = User(id=0, name="admin")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    build_login(app, service=service)
    client = app.test_client()
    res = client.post("/auth", json={"username": "admin", "password": "admin"})

    assert res.status_code == 200
    assert res.json["access_token"]

    service.authenticate.assert_called_once_with("admin", "admin")


@pytest.mark.unit_test
def test_auth_fail() -> None:
    service = Mock()
    service.authenticate.return_value = None

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret"
    build_login(app, service=service)
    client = app.test_client()
    res = client.post("/auth", json={"username": "admin", "password": "admin"})

    assert res.status_code == 401


@pytest.mark.unit_test
def test_user_fail() -> None:
    service = Mock()
    service.get_all.return_value = [User(id=1, name="user", role=Role.USER)]

    client, token = create_client(service)
    res = client.get("/users", headers=token)
    assert res.status_code == 403


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all.return_value = [User(id=1, name="user", role=Role.USER)]

    client, token = create_client(service, admin=True)
    res = client.get("/users", headers=token)
    assert res.status_code == 200
    assert res.json == [User(id=1, name="user", role=Role.USER).to_dict()]


@pytest.mark.unit_test
def test_user_create() -> None:
    service = Mock()

    client, token = create_client(service, admin=True)
    res = client.post(
        "/users",
        headers=token,
        json={"name": "a", "password": "b", "role": "USER"},
    )

    assert res.status_code == 200
    assert res.json == User(id=1, name="a", role=Role.USER).to_dict()
