from datetime import timedelta
from functools import wraps
from typing import List, Optional, Dict, Any, Callable, cast

from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, decode_token  # type: ignore

from antarest.common.config import Config
from antarest.login.model import User, Role


class Auth:
    ACCESS_TOKEN_DURATION = timedelta(minutes=15)
    REFRESH_TOKEN_DURATION = timedelta(hours=30)

    def __init__(
        self,
        config: Config,
        verify: Callable[[], None] = verify_jwt_in_request,  # Test only
        get_identity: Callable[
            [], Dict[str, Any]
        ] = get_jwt_identity,  # Test only
    ):

        self.disabled = config["security.disabled"]
        self.verify = verify
        self.get_identity = get_identity

    @staticmethod
    def get_current_user() -> Optional[User]:
        if "user" in g:
            return cast(User, g.user)

        return None

    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        token_data = decode_token(token)
        return User.from_dict(token_data["sub"])

    @staticmethod
    def invalidate() -> None:
        g.pop("user", None)

    def protected(
        self,
        roles: Optional[List[str]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def auth_nested(fn: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(fn)
            def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
                if self.disabled:
                    admin = User(id=0, name="admin", role=Role.ADMIN)
                    g.user = admin
                    return fn(*args, **kwargs)

                self.verify()
                user: Dict[str, Any] = self.get_identity()

                belong = roles is None
                belong = belong or user["role"] in (roles or [])

                if belong:
                    g.user = User.from_dict(user)
                    return fn(*args, **kwargs)
                else:
                    return "User unauthorized", 403

            return wrapper

        return auth_nested
