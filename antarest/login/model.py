from typing import Any, Optional

from werkzeug.security import (
    safe_str_cmp,
    generate_password_hash,
    check_password_hash,
)

from antarest.common.custom_types import JSON
from antarest.common.dto import DTO


class Role:
    ADMIN: str = "ADMIN"
    USER: str = "USER"


class Password:
    def __init__(self, pwd: str):
        self._pwd = generate_password_hash(pwd)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, str):
            return False
        return check_password_hash(self._pwd, other)  # type: ignore

    def __str__(self) -> str:
        return "*****"

    def __repr__(self) -> str:
        return self.__str__()


class User(DTO):
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        pwd: str = "",
        role: str = Role.USER,
    ):
        self.id = id
        self.role = role
        self.name = name
        self.password = Password(pwd)

    @staticmethod
    def from_dict(data: JSON) -> "User":
        return User(id=data.get("id"), name=data["name"], role=data["role"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name, "role": self.role}
