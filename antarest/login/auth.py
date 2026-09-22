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

import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Any, TypeAlias

from antarest.core.jwt import JWTUser
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.fastapi_jwt_auth import AuthJWT

logger = logging.getLogger(__name__)


ACCESS_TOKEN_DURATION = timedelta(minutes=15)
REFRESH_TOKEN_DURATION = timedelta(hours=30)
IdentityValidator: TypeAlias = Callable[[AuthJWT], JWTUser]


def get_user_from_token(token: str, jwt_manager: AuthJWT) -> JWTUser | None:
    try:
        token_data = jwt_manager._verified_token(token)
        return JWTUser.model_validate(from_json(token_data["sub"]))
    except Exception as e:
        logger.debug("Failed to retrieve user from token", exc_info=e)
    return None


class JwtSettings(AntaresBaseModel):
    authjwt_secret_key: str
    authjwt_token_location: tuple[str, ...]
    authjwt_access_token_expires: int | timedelta = ACCESS_TOKEN_DURATION
    authjwt_refresh_token_expires: int | timedelta = REFRESH_TOKEN_DURATION
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: Any = {"access", "refresh"}
    authjwt_cookie_csrf_protect: bool = True
