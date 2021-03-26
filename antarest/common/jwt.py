from enum import Enum
from typing import List

from dataclasses import dataclass

from antarest.common.custom_types import JSON


class JWTRole(Enum):
    ADMIN = "admin"
    RUNNER = "runner"
    WRITER = "writer"
    READER = "reader"


@dataclass
class JWTGroup:
    id: str
    name: str
    role: JWTRole

    @staticmethod
    def from_dict(data: JSON) -> "JWTGroup":
        return JWTGroup(id=data["id"], name=data["name"], role=data["role"])

    def to_dict(self) -> JSON:
        return {"id": self.id, "name": self.name, "role": str(self.role)}


@dataclass
class JWTUser:
    id: int
    name: str
    groups: List[JWTGroup]

    @staticmethod
    def from_dict(data: JSON) -> "JWTUser":
        return JWTUser(
            id=data["id"],
            name=data["name"],
            groups=[JWTGroup.from_dict(g) for g in data["groups"]],
        )

    def to_dict(self) -> JSON:
        return {
            "id": self.id,
            "name": self.name,
            "groups": [g.to_dict() for g in self.groups],
        }

    def is_admin(self) -> bool:
        return "admin" in [g.id for g in self.groups]
