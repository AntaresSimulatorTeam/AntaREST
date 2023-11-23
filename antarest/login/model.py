import logging
import typing as t
import uuid

import bcrypt
from pydantic.main import BaseModel
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Sequence, String  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.exc import IntegrityError  # type: ignore
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from sqlalchemy.orm import Session, relationship, sessionmaker  # type: ignore

from antarest.core.persistence import Base
from antarest.core.roles import RoleType

if t.TYPE_CHECKING:
    # avoid circular import
    from antarest.launcher.model import JobResult


logger = logging.getLogger(__name__)


GROUP_ID = "admin"
GROUP_NAME = "admin"

USER_ID = 1
USER_NAME = "admin"


class UserInfo(BaseModel):
    id: int
    name: str


class BotRoleCreateDTO(BaseModel):
    group: str
    role: int


class BotCreateDTO(BaseModel):
    name: str
    roles: t.List[BotRoleCreateDTO]
    is_author: bool = True


class UserCreateDTO(BaseModel):
    name: str
    password: str


class GroupDTO(BaseModel):
    id: t.Optional[str] = None
    name: str


class RoleCreationDTO(BaseModel):
    type: RoleType
    group_id: str
    identity_id: int


class RoleDTO(BaseModel):
    group_id: t.Optional[str]
    group_name: str
    identity_id: int
    type: RoleType


class IdentityDTO(BaseModel):
    id: int
    name: str
    roles: t.List[RoleDTO]


class RoleDetailDTO(BaseModel):
    group: GroupDTO
    identity: UserInfo
    type: RoleType


class BotIdentityDTO(BaseModel):
    id: int
    name: str
    isAuthor: bool
    roles: t.List[RoleDTO]


class BotDTO(UserInfo):
    owner: int
    is_author: bool


class UserRoleDTO(BaseModel):
    id: int
    name: str
    role: RoleType


class GroupDetailDTO(GroupDTO):
    users: t.List[UserRoleDTO]


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

    def __str__(self) -> str:
        return "*****"

    def __repr__(self) -> str:
        return self.__str__()


class Identity(Base):  # type: ignore
    """
    Abstract entity which represent generic user
    """

    __tablename__ = "identities"

    id = Column(Integer, Sequence("identity_id_seq"), primary_key=True)
    name = Column(String(255))
    type = Column(String(50))

    # Define a one-to-many relationship with `JobResult`.
    # If an identity is deleted, all the associated job results are detached from the identity.
    job_results: t.List["JobResult"] = relationship("JobResult", back_populates="owner", cascade="save-update, merge")

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

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


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

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


class Bot(Identity):
    """
    User hosted in this platform but using ony API (belongs to a user)
    """

    __tablename__ = "bots"

    id = Column(
        Integer,
        Sequence("identity_id_seq"),
        ForeignKey("identities.id"),
        primary_key=True,
    )
    # noinspection SpellCheckingInspection
    owner = Column(Integer, ForeignKey("identities.id", name="bots_owner_fkey"))
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

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.


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

    # Implementing a `__eq__` method is superfluous, since the default implementation
    # is to compare the identity of the objects using the primary key.

    def __repr__(self) -> str:
        return f"Group(id={self.id}, name={self.name})"


class Role(Base):  # type: ignore
    """
    Enable to link a user to a group with a specific role permission
    """

    __tablename__ = "roles"

    type = Column(Enum(RoleType))
    identity_id = Column(Integer, ForeignKey("identities.id"), primary_key=True)
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


def init_admin_user(engine: Engine, session_args: t.Mapping[str, bool], admin_password: str) -> None:
    with sessionmaker(bind=engine, **session_args)() as session:
        group = Group(id=GROUP_ID, name=GROUP_NAME)
        user = User(id=USER_ID, name=USER_NAME, password=Password(admin_password))
        role = Role(type=RoleType.ADMIN, identity=User(id=USER_ID), group=Group(id=GROUP_ID))

        existing_group = session.query(Group).get(group.id)
        if not existing_group:
            session.add(group)
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()  # Rollback any changes made before the error
                logger.error(f"IntegrityError: {e}")

        existing_user = session.query(User).get(user.id)
        if not existing_user:
            session.add(user)
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()  # Rollback any changes made before the error
                logger.error(f"IntegrityError: {e}")

        existing_role = session.query(Role).get((USER_ID, GROUP_ID))
        if not existing_role:
            role.group = session.merge(role.group)
            role.identity = session.merge(role.identity)
            session.add(role)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()  # Rollback any changes made before the error
            logger.error(f"IntegrityError: {e}")
