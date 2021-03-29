from typing import Optional

import werkzeug
from dataclasses import dataclass

from antarest.common.jwt import JWTUser


@dataclass
class RequestParameters:
    user: Optional[JWTUser] = None


class UserHasNotPermissionError(werkzeug.exceptions.Forbidden):
    pass
