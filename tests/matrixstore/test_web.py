# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.main import JwtSettings
from antarest.matrixstore.main import build_matrix_service
from antarest.matrixstore.model import MatrixDTO, MatrixInfoDTO
from fastapi_jwt_auth import AuthJWT
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

    build_matrix_service(
        app,
        user_service=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
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
    matrix_data = [[1, 2], [3, 4]]

    service = Mock()
    service.create.return_value = matrix

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/matrix",
        headers=create_auth_token(app),
        json=matrix_data,
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


@pytest.mark.unit_test
def test_delete() -> None:
    id = "123"
    service = Mock()
    service.delete.return_value = id

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/matrixdataset/123", headers=create_auth_token(app))
    assert res.status_code == 200


@pytest.mark.unit_test
def test_import() -> None:
    matrix_info = [MatrixInfoDTO(id="123", name="Matrix/matrix.txt")]
    service = Mock()
    service.create_by_importation.return_value = matrix_info

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/matrix/_import",
        headers=create_auth_token(app),
        files={"file": ("Matrix.zip", bytes(5), "application/zip")},
    )
    assert res.status_code == 200
    assert res.json() == matrix_info
