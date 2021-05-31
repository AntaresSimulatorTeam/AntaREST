from enum import Enum
from typing import List, Union

from dataclasses import dataclass, field

from antarest.common.custom_types import JSON
from antarest.common.roles import RoleType
from antarest.login.model import Group, User, Identity


@dataclass
class JWTGroup:
    """
    Sub JWT domain with groups data belongs to user
    """

    id: str
    name: str
    role: RoleType

    @staticmethod
    def from_dict(data: JSON) -> "JWTGroup":
        return JWTGroup(
            id=data["id"],
            name=data["name"],
            role=RoleType.from_dict(data["role"]),
        )

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name, "role": self.role.to_dict()}


@dataclass
class JWTUser:
    """
    JWT domain with user data.
    """

    id: int
    type: str
    impersonator: int
    groups: List[JWTGroup] = field(default_factory=lambda: list())

    @staticmethod
    def from_dict(data: JSON) -> "JWTUser":
        groups = data["groups"] if "groups" in data else []
        return JWTUser(
            id=data["id"],
            impersonator=data["impersonator"],
            type=data["type"],
            groups=[JWTGroup.from_dict(g) for g in groups],
        )

    def to_dict(self) -> JSON:
        return {
            "id": self.id,
            "impersonator": self.impersonator,
            "type": self.type,
            "groups": [g.to_dict() for g in self.groups],
        }

    def is_site_admin(self) -> bool:
        """
        Returns: true if connected user is admin

        """
        return "admin" in [g.id for g in self.groups]

    def is_group_admin(self, groups: Union[Group, List[Group]]) -> bool:
        """

        Args:
            groups: group or list of groups

        Returns: true if user is admin of one of groups given

        """
        if isinstance(groups, Group):
            return any(
                g.id == groups.id and g.role == RoleType.ADMIN
                for g in self.groups
            )

        return any(self.is_group_admin(g) for g in groups)

    def is_himself(self, user: Identity) -> bool:
        """
        Compare user
        Args:
            user: user to compare

        Returns: true if user are identical

        """
        return bool(self.id == user.id)
