from typing import Optional

from dataclasses import dataclass

from antarest.login.model import User


@dataclass
class RequestParameters:
    user: Optional[User] = None
