import json
import logging
from datetime import timedelta
from typing import List, Optional, Dict, Any, Callable, cast

from fastapi import Depends
from fastapi_jwt_auth import AuthJWT  # type: ignore

from antarest.common.config import Config
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType


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

    def get_current_user(self, auth_jwt: AuthJWT = Depends()) -> JWTUser:
        """
        Get logged user.
        Returns: jwt user data

        """
        if self.disabled:
            return JWTUser(
                id=1,
                impersonator=1,
                type="users",
                groups=[
                    JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
                ],
            )

        auth_jwt.jwt_required()

        user = JWTUser.from_dict(json.loads(auth_jwt.get_jwt_subject()))
        logging.getLogger(__name__).info(user)
        return user

    @staticmethod
    def get_user_from_token(token: str, jwt_manager: AuthJWT) -> JWTUser:
        token_data = jwt_manager._verified_token(token)
        return JWTUser.from_dict(json.loads(token_data["sub"]))
