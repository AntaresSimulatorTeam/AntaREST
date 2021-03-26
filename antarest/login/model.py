import uuid
from typing import Any, List

from dataclasses import dataclass
from sqlalchemy import Column, Integer, Sequence, String, Table, ForeignKey, Enum  # type: ignore
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTRole
from antarest.common.persistence import DTO, Base

users_groups = Table(
    "users_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("group_id", Integer, ForeignKey("groups.id")),
)


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


@dataclass
class User(Base):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    name = Column(String(255))
    _pwd = Column(String(255))

    @hybrid_property
    def password(self) -> Password:
        return Password(str(self._pwd))

    @password.setter  # type: ignore
    def password(self, pwd: Password) -> None:
        self._pwd = pwd.get()

    @staticmethod
    def from_dict(data: JSON) -> "User":
        return User(id=data.get("id"), name=data["name"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name}

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, User):
            return False
        return bool((o.id == self.id) and (o.name == self.name))


@dataclass
class Group(Base):  # type: ignore
    __tablename__ = "groups"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String(255))

    @staticmethod
    def from_dict(data: JSON) -> "Group":
        return Group(
            id=data.get("id"),
            name=data["name"],
        )

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name}


@dataclass
class Role(Base):  # type: ignore
    __tablename__ = "roles"

    type = Column(Enum(JWTRole))
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(String(36), ForeignKey("groups.id"), primary_key=True)
    user = relationship("User")
    group = relationship("Group")

    @staticmethod
    def from_dict(data: JSON) -> "Role":
        return Role(
            type=data["type"],
            user=User.from_dict(data["user"]),
            group=Group.from_dict(data["group"]),
        )

    def to_dict(self) -> JSON:
        return {
            "type": self.type,
            "user": self.user.to_dict(),
            "group": self.group.to_dict(),
        }
