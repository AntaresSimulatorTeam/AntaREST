# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import contextlib
import uuid
from typing import TYPE_CHECKING, Any, List, Mapping, Optional

import bcrypt
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Sequence, String
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.roles import RoleType
from antarest.core.serde import AntaresBaseModel

if TYPE_CHECKING:
    # avoid circular import
    from antarest.core.tasks.model import TaskJob
    from antarest.launcher.model import JobResult


GROUP_ID = "admin"
"""Unique ID of the administrator group."""

GROUP_NAME = "admin"
"""Name of the administrator group."""

ADMIN_ID = 1
"""Unique ID of the site administrator."""

ADMIN_NAME = "admin"
"""Name of the site administrator."""


class UserInfo(AntaresBaseModel):
    id: int
    name: str


class BotRoleCreateDTO(AntaresBaseModel):
    group: str
    role: int


class BotCreateDTO(AntaresBaseModel):
    name: str
    roles: List[BotRoleCreateDTO]
    is_author: bool = True


class UserCreateDTO(AntaresBaseModel):
    name: str
    password: str


class GroupDTO(AntaresBaseModel):
    id: str
    name: str


class GroupCreationDTO(AntaresBaseModel):
    name: str
    id: Optional[str] = None


class RoleCreationDTO(AntaresBaseModel):
    type: RoleType
    group_id: str
    identity_id: int


class RoleDTO(AntaresBaseModel):
    group_id: Optional[str]
    group_name: str
    identity_id: int
    type: RoleType


class IdentityDTO(AntaresBaseModel):
    id: int
    name: str
    roles: List[RoleDTO]


class RoleDetailDTO(AntaresBaseModel):
    group: GroupDTO
    identity: UserInfo
    type: RoleType


class BotIdentityDTO(AntaresBaseModel):
    id: int
    name: str
    isAuthor: bool
    roles: List[RoleDTO]


class BotDTO(UserInfo):
    owner: int
    is_author: bool


class UserRoleDTO(AntaresBaseModel):
    id: int
    name: str
    role: RoleType


class GroupDetailDTO(GroupDTO):
    users: List[UserRoleDTO]


class Password:
    """
    Domain Driven Object to force Secure by Design password
    """

    def __init__(self, pwd: str):
        self._pwd: bytes = pwd.encode() if "$2b" in pwd else bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())

    def get(self) -> str:
        return self._pwd.decode()

    def check(self, pwd: str) -> bool:
        return bcrypt.checkpw(pwd.encode(), self._pwd)

    @override
    def __str__(self) -> str:
        return "*****"

    @override
    def __repr__(self) -> str:
        return self.__str__()


class Identity(Base):  # type: ignore
    """
    Abstract entity which represent generic user
    """

    __tablename__ = "identities"

    id: Mapped[int] = mapped_column(Integer, Sequence("identity_id_seq"), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[Optional[str]] = mapped_column(String(50))

    # Define a one-to-many relationship with `JobResult`.
    # If an identity is deleted, all the associated job results are detached from the identity.
    job_results: Mapped[List["JobResult"]] = relationship(
        "JobResult", back_populates="owner", cascade="save-update, merge"
    )

    # Define a one-to-many relationship with `TaskJob`.
    # If an identity is deleted, all the associated task jobs are detached from the identity.
    owned_jobs: Mapped[List["TaskJob"]] = relationship("TaskJob", back_populates="owner", cascade="save-update, merge")

    def to_dto(self) -> UserInfo:
        return UserInfo(id=self.id, name=self.name)

    __mapper_args__ = {
        "polymorphic_identity": "identities",
        "polymorphic_on": type,
    }

    def get_impersonator(self) -> int:
        return int(self.id)


class User(Identity):
    """
    Basic user, hosted in this platform and using UI
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    _pwd: Mapped[Optional[str]] = mapped_column(String(255))

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

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


class UserLdap(Identity):
    """
    User using UI but hosted on LDAP server
    """

    __tablename__ = "users_ldap"

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String)
    firstname: Mapped[Optional[str]] = mapped_column(String)
    lastname: Mapped[Optional[str]] = mapped_column(String)
    __mapper_args__ = {
        "polymorphic_identity": "users_ldap",
    }

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


class Bot(Identity):
    """
    User hosted in this platform but using ony API (belongs to a user)
    """

    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    # noinspection SpellCheckingInspection
    owner: Mapped[int] = mapped_column(Integer, ForeignKey("identities.id", name="bots_owner_fkey"))
    is_author: Mapped[bool] = mapped_column(Boolean(), default=True)

    @override
    def get_impersonator(self) -> int:
        return int(self.id if self.is_author else self.owner)

    __mapper_args__ = {
        "polymorphic_identity": "bots",
        "inherit_condition": id == Identity.id,
    }

    @override
    def to_dto(self) -> BotDTO:
        return BotDTO(
            id=self.id,
            name=self.name,
            owner=self.owner,
            is_author=self.is_author,
        )

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


class Group(Base):  # type: ignore
    """
    Group of users
    """

    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))

    def to_dto(self) -> GroupDTO:
        return GroupDTO(id=self.id, name=self.name)

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.

    @override
    def __repr__(self) -> str:
        return f"Group(id={self.id}, name={self.name})"


class Role(Base):  # type: ignore
    """
    Enable to link a user to a group with a specific role permission
    """

    __tablename__ = "roles"

    type: Mapped[RoleType] = mapped_column(Enum(RoleType))
    identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("identities.id"), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("groups.id"), primary_key=True)
    identity: Mapped["Identity"] = relationship("Identity")
    group: Mapped["Group"] = relationship("Group")

    def to_dto(self) -> RoleDetailDTO:
        return RoleDetailDTO(
            type=self.type,
            group=self.group.to_dto(),
            identity=self.identity.to_dto(),
        )


class CredentialsDTO(AntaresBaseModel):
    user: int
    access_token: str
    refresh_token: str


def init_admin_user(engine: Engine, session_args: Mapping[str, Any], admin_password: str) -> None:
    """
    Create the default admin user, group and role if they do not already exist in the database.

    Args:
        engine: The database engine (SQLAlchemy connection to SQLite or PostgreSQL).
        session_args: The session arguments (SQLAlchemy session arguments).
        admin_password: The admin password extracted from the configuration file.
    """
    make_session = sessionmaker(bind=engine, **session_args)
    with make_session() as session:
        group = Group(id=GROUP_ID, name=GROUP_NAME)
        with contextlib.suppress(IntegrityError):
            session.add(group)
            session.commit()

    with make_session() as session:
        user = User(id=ADMIN_ID, name=ADMIN_NAME, password=Password(admin_password))
        with contextlib.suppress(IntegrityError):
            session.add(user)
            session.commit()

    with make_session() as session:
        role = Role(type=RoleType.ADMIN, identity_id=ADMIN_ID, group_id=GROUP_ID)
        with contextlib.suppress(IntegrityError):
            session.add(role)
            session.commit()
