from typing import Any, Optional, Union

from sqlalchemy import Column, Integer, Sequence, String  # type: ignore
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from werkzeug.security import (
    safe_str_cmp,
    generate_password_hash,
    check_password_hash,
)

from antarest.common.custom_types import JSON
from antarest.common.dto import DTO, Base


class Role:
    ADMIN: str = "ADMIN"
    USER: str = "USER"


class Password:
    def __init__(self, pwd: str):
        self._pwd: str = (
            pwd if "pbkdf2:sha256:" in pwd else generate_password_hash(pwd)
        )

    def get(self) -> str:
        return self._pwd

    def check(self, pwd: str) -> bool:
        return check_password_hash(self._pwd, pwd)  # type: ignore

    def __str__(self) -> str:
        return "*****"

    def __repr__(self) -> str:
        return self.__str__()


class User(DTO, Base):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    name = Column(String(255))
    role = Column(String(255))
    _pwd = Column(String(255))

    @hybrid_property
    def password(self) -> Password:
        return Password(str(self._pwd))

    @password.setter  # type: ignore
    def password(self, pwd: Password) -> None:
        self._pwd = pwd.get()

    @staticmethod
    def from_dict(data: JSON) -> "User":
        return User(id=data.get("id"), name=data["name"], role=data["role"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name, "role": self.role}

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, User):
            return False
        return bool(
            (o.id == self.id)
            and (o.name == self.name)
            and (o.role == self.role)
        )
