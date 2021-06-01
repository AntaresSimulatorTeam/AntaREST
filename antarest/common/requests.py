from typing import Optional

import werkzeug
from dataclasses import dataclass

from antarest.common.jwt import JWTUser


@dataclass
class RequestParameters:
    """
    DTO object to handle data inside request to send to service
    """

    user: Optional[JWTUser] = None

    def get_user_id(self) -> str:
        return str(self.user.id) if self.user else "Unknown"


class UserHasNotPermissionError(werkzeug.exceptions.Forbidden):
    pass
