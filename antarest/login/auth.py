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
from typing import Annotated, Any, AsyncGenerator, Callable, Coroutine, Optional, Tuple, TypeAlias, Union

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


IdentityValidator: TypeAlias = Callable[[AuthJWT], JWTUser]


def _validate_jwt(auth_jwt: AuthJWT) -> JWTUser:
    auth_jwt.jwt_required()
    return JWTUser.model_validate(from_json(auth_jwt.get_jwt_subject()))


class Auth:
    """
    Context object to retrieve data present in jwt
    """

    ACCESS_TOKEN_DURATION = timedelta(minutes=15)
    REFRESH_TOKEN_DURATION = timedelta(hours=30)

    def __init__(
        self,
        config: Config,
        validate_identity: IdentityValidator = _validate_jwt,
    ):
        self.disabled = config.security.disabled
        self.validate_identity = validate_identity

    def create_auth_function(
        self,
    ) -> Callable[[Scope], Coroutine[Any, Any, Tuple[str, str]]]:
        async def auth(scope: Scope) -> Tuple[str, str]:
            auth_jwt = AuthJWT(Request(scope))
            user = self._get_current_user(auth_jwt)
            return str(user.id), "admin" if user.is_site_admin() else "default"

        return auth

    def _get_current_user(self, auth_jwt: AuthJWT) -> JWTUser:
        """
        Get logged user.
        Returns: jwt user data

        """
        if self.disabled:
            return DEFAULT_ADMIN_USER
        return self.validate_identity(auth_jwt)

    def required(self) -> Any:
        """
        A FastAPI dependency to require authentication.
        Depends itself on AuthJWT dependency.
        Will also set the logged-in user context for the current request.

        Notes:
            Implementation note:
            The dependency MUST be async, otherwise it's executed in a thread which will
            generally not be the same as the one of the request.
        """
        return Depends(self._yield_current_user)

    async def _yield_current_user(self, auth_jwt: Annotated[AuthJWT, Depends(AuthJWT)]) -> AsyncGenerator[None, None]:
        user = self._get_current_user(auth_jwt)
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
