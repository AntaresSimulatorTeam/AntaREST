from typing import Any, Optional

from dataclasses import dataclass

from antarest.login.model import User


@dataclass
class StorageServiceParameters:
    depth: int = 3
    user: Optional[User] = None
