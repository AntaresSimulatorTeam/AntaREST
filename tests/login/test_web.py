from unittest.mock import Mock

import pytest
from flask import Flask

from antarest.login.main import build_login
from antarest.login.model import User


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
