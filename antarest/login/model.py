import uuid
from dataclasses import dataclass
from typing import Any, List, Optional

import bcrypt
from pydantic.main import BaseModel
from sqlalchemy import Column, Integer, Sequence, String, ForeignKey, Enum, Boolean  # type: ignore
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.model import JSON
from antarest.core.persistence import Base
from antarest.core.roles import RoleType


class UserInfo(BaseModel):
    id: int
    name: str


class BotRoleCreateDTO(BaseModel):
    group: str
    role: int


class BotCreateDTO(BaseModel):
    name: str
    roles: List[BotRoleCreateDTO]
    is_author: bool = True


class UserCreateDTO(BaseModel):
    name: str
    password: str


class GroupDTO(BaseModel):
    id: Optional[str] = None
    name: str


class RoleCreationDTO(BaseModel):
    type: RoleType
    group_id: str
    identity_id: int


class RoleDTO(BaseModel):
    group_id: Optional[str]
    group_name: str
    identity_id: int
    type: RoleType


class IdentityDTO(BaseModel):
    id: int
    name: str
    roles: List[RoleDTO]


class RoleDetailDTO(BaseModel):
    group: GroupDTO
    identity: UserInfo
    type: RoleType


class BotIdentityDTO(BaseModel):
    id: int
    name: str
    isAuthor: bool
    roles: List[RoleDTO]


class BotDTO(UserInfo):
    owner: int
    is_author: bool


class UserRoleDTO(BaseModel):
    id: int
    name: str
    role: RoleType


class UserGroup(BaseModel):
    group: GroupDTO
    users: List[UserRoleDTO]


class Password:
    """
    Domain Driven Object to force Secure by Design password
    """

    def __init__(self, pwd: str):
        self._pwd: bytes = (
            pwd.encode()
            if "$2b" in pwd
            else bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
        )

    def get(self) -> str:
        return self._pwd.decode()

    def check(self, pwd: str) -> bool:
        return bcrypt.checkpw(pwd.encode(), self._pwd)

    def __str__(self) -> str:
        return "*****"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class Identity(Base):  # type: ignore
    """
    Abstract entity which represent generic user
    """

    __tablename__ = "identities"

    id = Column(Integer, Sequence("identity_id_seq"), primary_key=True)
    name = Column(String(255))
    type = Column(String(50))

    def to_dto(self) -> UserInfo:
        return UserInfo(id=self.id, name=self.name)

    __mapper_args__ = {
        "polymorphic_identity": "identities",
        "polymorphic_on": type,
    }

    def get_impersonator(self) -> int:
        return int(self.id)


@dataclass
class User(Identity):
    """
    Basic user, hosted in this plateform and using UI
    """

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
    def from_dto(data: UserInfo) -> "User":
        return User(id=data.id, name=data.name)

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, User):
            return False
        return bool((o.id == self.id) and (o.name == self.name))


@dataclass
class UserLdap(Identity):
    """
    User using UI but hosted on LDAP server
    """

    __tablename__ = "users_ldap"

    id = Column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    external_id = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    __mapper_args__ = {
        "polymorphic_identity": "users_ldap",
    }

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, UserLdap):
            return False
        return bool((o.id == self.id) and (o.name == self.name))


@dataclass
class Bot(Identity):
    """
    User hosted in this platform but using ony API (belongs to an user)
    """

    __tablename__ = "bots"

    id = Column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    owner = Column(
        Integer, ForeignKey("identities.id", name="bots_owner_fkey")
    )
    is_author = Column(Boolean(), default=True)

    def get_impersonator(self) -> int:
        return int(self.id if self.is_author else self.owner)

    __mapper_args__ = {
        "polymorphic_identity": "bots",
        "inherit_condition": id == Identity.id,
    }

    def to_dto(self) -> BotDTO:
        return BotDTO(
            id=self.id,
            name=self.name,
            owner=self.owner,
            is_author=self.is_author,
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Bot):
            return False
        return self.to_dto().dict() == other.to_dto().dict()


@dataclass
class Group(Base):  # type: ignore
    """
    Group of users
    """

    __tablename__ = "groups"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String(255))

    def to_dto(self) -> GroupDTO:
        return GroupDTO(id=self.id, name=self.name)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Group):
            return False

        return bool(self.id == other.id and self.name == other.name)


@dataclass
class Role(Base):  # type: ignore
    """
    Enable to link a user to a group with a specific role permission
    """

    __tablename__ = "roles"

    type = Column(Enum(RoleType))
    identity_id = Column(
        Integer, ForeignKey("identities.id"), primary_key=True
    )
    group_id = Column(String(36), ForeignKey("groups.id"), primary_key=True)
    identity = relationship("Identity")
    group = relationship("Group")

    def to_dto(self) -> RoleDetailDTO:
        return RoleDetailDTO(
            type=self.type,
            group=self.group.to_dto(),
            identity=self.identity.to_dto(),
        )


class CredentialsDTO(BaseModel):
    user: int
    access_token: str
    refresh_token: str
