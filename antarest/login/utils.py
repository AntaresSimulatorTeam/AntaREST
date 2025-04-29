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
from contextvars import ContextVar
from re import escape
from typing import Iterator, Optional

from antarest.core.jwt import JWTUser
from antarest.core.requests import MustBeAuthenticatedError

_current_user: ContextVar[Optional[JWTUser]] = ContextVar("_current_user", default=None)


def get_current_user() -> Optional[JWTUser]:
    current_user = _current_user.get()
    return current_user


def require_current_user() -> JWTUser:
    if user := get_current_user():
        return user
    raise MustBeAuthenticatedError()


def get_user_id() -> str:
    user = get_current_user()
    return str(escape(str(user.id))) if user else "Unknown"


@contextlib.contextmanager
def current_user_context(token: Optional[JWTUser]) -> Iterator[JWTUser | None]:
    reset_token = _current_user.set(token)
    try:
        yield _current_user.get()
    finally:
        _current_user.reset(reset_token)
