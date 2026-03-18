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
from typing import Iterable

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config


@pytest.fixture
def auth_disabled_app(app: FastAPI) -> Iterable[FastAPI]:
    # Temporarily disable security by mutating the frozen config object in-place
    config: Config = app.state.config
    original_disabled = config.security.disabled
    object.__setattr__(config.security, "disabled", True)
    yield app
    object.__setattr__(config.security, "disabled", original_disabled)


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
