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

import contextlib
import typing as t
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from typing_extensions import override

from antarest.core.jwt import JWTUser
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth

_current_user: ContextVar[t.Optional[JWTUser]] = ContextVar("_current_user", default=None)


class CurrentUserMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, auth: Auth) -> None:
        super().__init__(app)
        self.auth = auth

    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        global _current_user

        try:
            auth_jwt = AuthJWT(request)
            # TODO: here we turn the user token into a jwt_user object.
            # this process exists in other places and must be done once instead
            jwt_user = self.auth.get_current_user(auth_jwt)  # fail when no cookies are provided
        except Exception:
            jwt_user = None

        _current_user.set(jwt_user)

        with current_user_context(jwt_user):
            return await call_next(request)


def get_current_user() -> Optional[JWTUser]:
    current_user = _current_user.get()
    return current_user


@contextlib.contextmanager
def current_user_context(token: Optional[JWTUser]) -> t.Iterator[JWTUser | None]:
    global _current_user
    _current_user.set(token)

    yield _current_user.get()

    _current_user.set(None)
