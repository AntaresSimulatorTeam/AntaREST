from typing import Any, Optional

from werkzeug.security import (
    safe_str_cmp,
    generate_password_hash,
    check_password_hash,
)

from antarest.common.custom_types import JSON


class Password:
    def __init__(self, pwd: str):
        self._pwd = generate_password_hash(pwd)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, str):
            return False
        return check_password_hash(self._pwd, other)  # type: ignore


class User:
    def __init__(
        self, id: Optional[int] = None, name: str = "", pwd: str = ""
    ):
        self.id = id
        self.name = name
        self.password = Password(pwd)

    def from_dict(self, data: JSON) -> "User":
        return User(id=data["id"], name=data["id"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name}
