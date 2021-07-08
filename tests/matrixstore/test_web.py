from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi_jwt_auth import AuthJWT
from starlette.testclient import TestClient

from antarest.common.config import Config, SecurityConfig
from antarest.main import JwtSettings
from antarest.matrixstore.main import build_matrixstore
from antarest.matrixstore.model import MatrixDTO
from tests.login.test_web import create_auth_token


def create_app(service: Mock, auth_disabled=False) -> FastAPI:
    app = FastAPI(title=__name__)

    @AuthJWT.load_config
    def get_config():
        return JwtSettings(
            authjwt_secret_key="super-secret",
            authjwt_token_location=("headers", "cookies"),
            authjwt_denylist_enabled=False,
        )

    build_matrixstore(
        app,
        user_service=Mock(),
        service=service,
        config=Config(
            resources_path=Path(),
            security=SecurityConfig(disabled=auth_disabled),
        ),
    )
    return app


@pytest.mark.unit_test
def test_create() -> None:
    matrix = MatrixDTO(
        id="id",
        width=2,
        height=2,
        created_at=0,
        index=["1", "2"],
        columns=["a", "b"],
        data=[[1, 2], [3, 4]],
    )

    service = Mock()
    service.create.return_value = matrix

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/matrix", headers=create_auth_token(app), json=matrix.dict()
    )
    assert res.status_code == 200
    assert res.json() == matrix.dict()


@pytest.mark.unit_test
def test_get() -> None:
    matrix = MatrixDTO(
        id="123",
        width=2,
        height=2,
        created_at=0,
        index=["1", "2"],
        columns=["a", "b"],
        data=[[1, 2], [3, 4]],
    )

    service = Mock()
    service.get.return_value = matrix

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/matrix/123", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == matrix.dict()
    service.get.assert_called_once_with("123")
