import enum
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
from antarest.common.roles import RoleType
from antarest.common.persistence import Base


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
class Identity(Base):  # type: ignore
    __tablename__ = "identities"

    id = Column(Integer, Sequence("identity_id_seq"), primary_key=True)
    name = Column(String(255))
    type = Column(String(50))

    @staticmethod
    def from_dict(data: JSON) -> "Identity":
        return Identity(
            id=data["id"],
            name=data["name"],
        )

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name}

    __mapper_args__ = {
        "polymorphic_identity": "identities",
        "polymorphic_on": type,
    }


@dataclass
class User(Identity):  # type: ignore
    __tablename__ = "users"

    id = Column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    _pwd = Column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "users",
    }

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

    type = Column(Enum(RoleType))
    identity_id = Column(
        Integer, ForeignKey("identities.id"), primary_key=True
    )
    group_id = Column(String(36), ForeignKey("groups.id"), primary_key=True)
    identity = relationship("Identity")
    group = relationship("Group")

    @staticmethod
    def from_dict(data: JSON) -> "Role":
        return Role(
            type=RoleType.from_dict(data["type"]),
            identity=User.from_dict(data["user"]),
            group=Group.from_dict(data["group"]),
        )

    def to_dict(self) -> JSON:
        return {
            "type": self.type.to_dict(),
            "user": self.identity.to_dict(),
            "group": self.group.to_dict(),
        }
