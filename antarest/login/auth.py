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

import logging
from datetime import timedelta
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, Optional, Tuple, Union

from fastapi import Depends
from ratelimit.types import Scope  # type: ignore
from starlette.requests import Request

from antarest.core.config import Config
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.utils import current_user_context

logger = logging.getLogger(__name__)


class Auth:
    """
    Context object to retrieve data present in jwt
    """

    ACCESS_TOKEN_DURATION = timedelta(minutes=15)
    REFRESH_TOKEN_DURATION = timedelta(hours=30)

    def __init__(
        self,
        config: Config,
        verify: Callable[[], None] = AuthJWT().jwt_required,  # Test only
        get_identity: Callable[[], Dict[str, Any]] = AuthJWT().get_raw_jwt,  # Test only
    ):
        self.disabled = config.security.disabled
        self.verify = verify
        self.get_identity = get_identity

    def create_auth_function(
        self,
    ) -> Callable[[Scope], Coroutine[Any, Any, Tuple[str, str]]]:
        async def auth(scope: Scope) -> Tuple[str, str]:
            auth_jwt = AuthJWT(Request(scope))
            user = self._get_current_user(auth_jwt)
            return str(user.id), "admin" if user.is_site_admin() else "default"

        return auth

    def _get_current_user(self, auth_jwt: AuthJWT = Depends()) -> JWTUser:
        """
        Get logged user.
        Returns: jwt user data

        """
        if self.disabled:
            return DEFAULT_ADMIN_USER

        auth_jwt.jwt_required()
        return JWTUser.model_validate(from_json(auth_jwt.get_jwt_subject()))

    def required(self) -> Any:
        """
        A FastAPI dependency to require authentication.
        Will also set the logged-in user context for the current request.

        Notes:
            Implementation note:
            The dependency MUST be async, otherwise it's executed in a thread which will
            generally not be the same as the one of the request.
        """
        return Depends(self._yield_current_user)

    async def _yield_current_user(self, auth_jwt: AuthJWT = Depends()) -> AsyncGenerator[None, None]:
        user = self._get_current_user(auth_jwt)  # fail when no cookies are provided
        with current_user_context(user):
            yield

    @staticmethod
    def get_user_from_token(token: str, jwt_manager: AuthJWT) -> Optional[JWTUser]:
        try:
            token_data = jwt_manager._verified_token(token)
            return JWTUser.model_validate(from_json(token_data["sub"]))
        except Exception as e:
            logger.debug("Failed to retrieve user from token", exc_info=e)
        return None


class JwtSettings(AntaresBaseModel):
    authjwt_secret_key: str
    authjwt_token_location: Tuple[str, ...]
    authjwt_access_token_expires: Union[int, timedelta] = Auth.ACCESS_TOKEN_DURATION
    authjwt_refresh_token_expires: Union[int, timedelta] = Auth.REFRESH_TOKEN_DURATION
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: Any = {"access", "refresh"}
    authjwt_cookie_csrf_protect: bool = True
