import typing as t
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from typing_extensions import override

from antarest.core.jwt import JWTUser
from antarest.core.serialization import from_json
from antarest.fastapi_jwt_auth import AuthJWT

_current_user: ContextVar[t.Optional[AuthJWT]] = ContextVar("_current_user", default=None)


class CurrentUserMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        global _current_user
        auth_jwt = AuthJWT(Request(request.scope))
        _current_user.set(auth_jwt)

        response = await call_next(request)
        return response


def get_current_user() -> Optional[JWTUser]:
    auth_jwt = _current_user.get()
    if auth_jwt:
        json_data = from_json(auth_jwt.get_jwt_subject())
        current_user = JWTUser.model_validate(json_data)
    else:
        current_user = None
    return current_user
