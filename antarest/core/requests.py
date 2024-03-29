from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException
from markupsafe import escape
from ratelimit import Rule  # type: ignore

from antarest.core.jwt import JWTUser

RATE_LIMIT_CONFIG = {
    r"^/v1/launcher/run": [
        Rule(second=1, minute=20),
    ],
    r"^/v1/watcher/_scan": [
        Rule(minute=2),
    ],
}


@dataclass
class RequestParameters:
    """
    DTO object to handle data inside request to send to service
    """

    user: Optional[JWTUser] = None

    def get_user_id(self) -> str:
        return str(escape(str(self.user.id))) if self.user else "Unknown"


class UserHasNotPermissionError(HTTPException):
    def __init__(self, msg: str = "Permission denied") -> None:
        super().__init__(status_code=403, detail=msg)


class MustBeAuthenticatedError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Permission denied")
