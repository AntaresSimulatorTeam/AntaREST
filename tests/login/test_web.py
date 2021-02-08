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
        config=Config({"main": {"res": Path()}}),
        engine=Mock(),
    )
    return app.test_client()


def get_token(role: str = Role.USER) -> Dict[str, str]:
    if role == Role.USER:
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTIxNzU4MDYsIm5iZiI6MTYxMjE3NTgwNiwianRpIjoiMzkzM2M0MTItZGI2NS00YjUwLTk5ZGMtYzJlYjgxMTBkNTlhIiwiZXhwIjo5OTk5OTk5OTk5LCJpZGVudGl0eSI6eyJpZCI6MCwibmFtZSI6ImFkbWluIiwicm9sZSI6IlVTRVIifSwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIn0.uNpLBLA-tEM-TB8dv4wrj3KLGVQL9A07wjE3835GDjM"
    elif role == Role.ADMIN:
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTIxNzU4MDYsIm5iZiI6MTYxMjE3NTgwNiwianRpIjoiMzkzM2M0MTItZGI2NS00YjUwLTk5ZGMtYzJlYjgxMTBkNTlhIiwiZXhwIjo5OTk5OTk5OTk5LCJpZGVudGl0eSI6eyJpZCI6MCwibmFtZSI6ImFkbWluIiwicm9sZSI6IkFETUlOIn0sImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.Gbxhmz6XSke0OZ2-fwRFKoh8LOrFj0pbJeR3Vfj536Q"
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = User(id=0, name="admin")

    client = create_client(service)
    res = client.post("/auth", json={"username": "admin", "password": "admin"})

    assert res.status_code == 200
    assert res.json["access_token"]

    service.authenticate.assert_called_once_with("admin", "admin")


@pytest.mark.unit_test
def test_auth_fail() -> None:
    service = Mock()
    service.authenticate.return_value = None

    client = create_client(service)
    res = client.post("/auth", json={"username": "admin", "password": "admin"})

    assert res.status_code == 401


@pytest.mark.unit_test
def test_user_fail() -> None:
    service = Mock()
    service.get_all_users.return_value = [
        User(id=1, name="user", role=Role.USER)
    ]

    client = create_client(service)
    res = client.get("/users", headers=get_token())
    assert res.status_code == 403


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all_users.return_value = [
        User(id=1, name="user", role=Role.USER)
    ]

    client = create_client(service)
    res = client.get("/users", headers=get_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == [User(id=1, name="user", role=Role.USER).to_dict()]


@pytest.mark.unit_test
def test_user_create() -> None:
    user = User(id=1, name="a", role=Role.USER, password=Password("b"))
    service = Mock()
    service.save_user.return_value = user

    client = create_client(service)
    res = client.post(
        "/users",
        headers=get_token(Role.ADMIN),
        json={"name": "a", "password": "b", "role": "USER"},
    )

    assert res.status_code == 200
    assert res.json == user.to_dict()


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    client = create_client(service)
    res = client.delete("/users/0", headers=get_token(Role.ADMIN))

    assert res.status_code == 200
    service.delete_user.assert_called_once_with(0)


@pytest.mark.unit_test
def test_groups_fail() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id=1, name="group")]

    client = create_client(service)
    res = client.get("/groups", headers=get_token())
    assert res.status_code == 403


@pytest.mark.unit_test
def test_group() -> None:
    service = Mock()
    service.get_all_groups.return_value = [Group(id=1, name="group")]

    client = create_client(service)
    res = client.get("/groups", headers=get_token(Role.ADMIN))
    assert res.status_code == 200
    assert res.json == [Group(id=1, name="group").to_dict()]


@pytest.mark.unit_test
def test_user_create() -> None:
    group = Group(id=1, name="group")
    service = Mock()
    service.save_group.return_value = group

    client = create_client(service)
    res = client.post(
        "/groups",
        headers=get_token(Role.ADMIN),
        json={"name": "group"},
    )

    assert res.status_code == 200
    assert res.json == group.to_dict()


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    client = create_client(service)
    res = client.delete("/groups/0", headers=get_token(Role.ADMIN))

    assert res.status_code == 200
    service.delete_group.assert_called_once_with(0)
