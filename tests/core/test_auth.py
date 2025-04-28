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

from fastapi import FastAPI

from antarest.core.config import Config, SecurityConfig
from antarest.login.auth import Auth
from antarest.login.model import RoleType


def create_app() -> FastAPI:
    app = FastAPI(title=__name__)
    return app


def build(security_disabled: bool = False, admin: bool = False) -> Auth:
    get_identity = Mock()
    get_identity.return_value = {
        "id": 0,
        "impersonator": 0,
        "type": "users",
        "groups": [
            {
                "id": "admin" if admin else "group",
                "name": "group",
                "role": RoleType.ADMIN.value,
            }
        ],
    }

    config = Config(security=SecurityConfig(disabled=security_disabled))

    return Auth(config=config, verify=Mock(), get_identity=get_identity)


def endpoint():
    return "Hello", 200


def test_local() -> None:
    auth = build(security_disabled=True)

    assert auth._get_current_user() is not None


# def test_admin_matched() -> None:
#     auth = build(security_disabled=False, admin=True)
#
#
#     with create_app().app_context():
#         res, code = auth.protected(admin=True)(endpoint)()
#     assert code == 200
#
#
# def test_fail() -> None:
#     auth = build(security_disabled=False)
#
#     with create_app().app_context():
#         res, code = auth.protected(admin=True)(endpoint)()
#     assert code == 403
#
#
# def test_no_filter() -> None:
#     auth = build(security_disabled=False)
#
#     with create_app().app_context():
#         res, code = auth.protected()(endpoint)()
#     assert code == 200
