from enum import Enum
from typing import List

from dataclasses import dataclass

from antarest.common.custom_types import JSON


@dataclass
class Role(Enum):
    ADMIN = "admin"
    RUNNER = "runner"
    WRITER = "writer"
    READER = "reader"


@dataclass
class Group:
    id: str
    name: str
    role: Role

    @staticmethod
    def from_dict(data: JSON) -> "Group":
        return Group(id=data["id"], name=data["name"], role=data["role"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name, "role": self.role}


@dataclass
class User:
    id: int
    name: str
    groups: List[Group]

    @staticmethod
    def from_dict(data: JSON) -> "User":
        return User(
            id=data["id"],
            name=data["name"],
            groups=[Group.from_dict(g) for g in data["groups"]],
        )

    def to_dict(self) -> JSON:
        return {
            "id": self.id,
            "name": self.name,
            "groups": [g.to_dict() for g in self.groups],
        }
