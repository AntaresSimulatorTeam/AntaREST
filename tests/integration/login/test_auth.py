# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from collections.abc import Iterable

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.dependencies import get_config


@pytest.fixture
def auth_disabled_app(app: FastAPI) -> Iterable[FastAPI]:
    # Note: important to reset the dependency overrides after use, for subsequent tests

    config = Config(security=SecurityConfig(disabled=True))
    app.dependency_overrides[get_config] = lambda: config
    yield app
    app.dependency_overrides.clear()


def test_disable_auth(auth_disabled_app: FastAPI, client: TestClient):
    client = TestClient(auth_disabled_app)

    res = client.get("/v1/users")
    assert res.status_code == 200
    assert res.json() == [{"id": 1, "name": "admin"}]


def test_enable_auth_requires_authentication(app: FastAPI, client: TestClient, user_access_token: str):
    # Fails without authentication
    res = client.get("/v1/users")
    assert res.status_code == 401

    # Succeeds with access token
    res = client.get("/v1/users", headers={"Authorization": f"Bearer {user_access_token}"})
    assert res.status_code == 200
    assert res.json() == [{"id": 2, "name": "George"}]
