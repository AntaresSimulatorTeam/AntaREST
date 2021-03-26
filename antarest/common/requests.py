from typing import Optional

from dataclasses import dataclass

from antarest.common.jwt import JWTUser


@dataclass
class RequestParameters:
    user: Optional[JWTUser] = None
