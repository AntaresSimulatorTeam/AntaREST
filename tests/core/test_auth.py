# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from unittest.mock import Mock

from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth, IdentityValidator
from antarest.login.utils import get_current_user, require_current_user


def create_app(security_disabled: bool, identity_validator: IdentityValidator) -> FastAPI:
    auth = Auth(Config(security=SecurityConfig(disabled=security_disabled)), identity_validator)
    app = FastAPI(title=__name__, dependencies=[auth.required()])

    @app.get("/user")
    def get_user() -> int:
        return require_current_user().id

    return app


def test_disabled_auth_should_use_admin_user():
    def _should_not_reach(jwt: AuthJWT) -> JWTUser:
        raise AssertionError("Should not reach")

    app = create_app(security_disabled=True, identity_validator=_should_not_reach)

    client = TestClient(app)
    assert get_current_user() is None
    res = client.get("/user")

    assert get_current_user() is None
    assert res.json() == DEFAULT_ADMIN_USER.id


def test_auth_should_set_current_user():
    # create an identity validator which returns admin then another user
    user = JWTUser(id=12, type="user", impersonator=36, groups=[])
    identidy_validator = Mock()
    identidy_validator.side_effect = (DEFAULT_ADMIN_USER, user)

    app = create_app(security_disabled=False, identity_validator=identidy_validator)

    client = TestClient(app)
    res = client.get("/user")
    assert res.json() == DEFAULT_ADMIN_USER.id
    res = client.get("/user")
    assert res.json() == 12


def test_auth_should_return_status_code_on_exception():
    def _raise_401(jwt: AuthJWT) -> JWTUser:
        raise HTTPException(status_code=401)

    app = create_app(security_disabled=False, identity_validator=_raise_401)

    client = TestClient(app)
    res = client.get("/user")
    assert res.status_code == 401
