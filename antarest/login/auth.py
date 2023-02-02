import json
import logging
from datetime import timedelta
from typing import Dict, Any, Callable, Tuple, Union, Optional, Coroutine

from fastapi import Depends
from fastapi_jwt_auth import AuthJWT  # type: ignore
from pydantic import BaseModel
from ratelimit.types import Scope  # type: ignore
from starlette.requests import Request

from antarest.core.config import Config
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER

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
        get_identity: Callable[
            [], Dict[str, Any]
        ] = AuthJWT().get_raw_jwt,  # Test only
    ):
        self.disabled = config.security.disabled
        self.verify = verify
        self.get_identity = get_identity

    def create_auth_function(
        self,
    ) -> Callable[[Scope], Coroutine[Any, Any, Tuple[str, str]]]:
        async def auth(scope: Scope) -> Tuple[str, str]:
            auth_jwt = AuthJWT(Request(scope))
            user = self.get_current_user(auth_jwt)
            return str(user.id), "admin" if user.is_site_admin() else "default"

        return auth

    def get_current_user(self, auth_jwt: AuthJWT = Depends()) -> JWTUser:
        """
        Get logged user.
        Returns: jwt user data

        """
        if self.disabled:
            return DEFAULT_ADMIN_USER

        auth_jwt.jwt_required()

        user = JWTUser.parse_obj(json.loads(auth_jwt.get_jwt_subject()))
        return user

    @staticmethod
    def get_user_from_token(
        token: str, jwt_manager: AuthJWT
    ) -> Optional[JWTUser]:
        try:
            token_data = jwt_manager._verified_token(token)
            return JWTUser.parse_obj(json.loads(token_data["sub"]))
        except Exception as e:
            logger.debug("Failed to retrieve user from token", exc_info=e)
        return None


class JwtSettings(BaseModel):
    authjwt_secret_key: str
    authjwt_token_location: Tuple[str, ...]
    authjwt_access_token_expires: Union[
        int, timedelta
    ] = Auth.ACCESS_TOKEN_DURATION
    authjwt_refresh_token_expires: Union[
        int, timedelta
    ] = Auth.REFRESH_TOKEN_DURATION
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: Any = {"access", "refresh"}
    authjwt_cookie_csrf_protect: bool = True
