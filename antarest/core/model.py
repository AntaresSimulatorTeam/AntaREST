import enum
from typing import Any, Dict, List, Union, Optional

from dataclasses import dataclass, field

JSON = Dict[str, Any]
ELEMENT = Union[str, int, float, bool, bytes]
SUB_JSON = Union[ELEMENT, JSON, List, None]


class PublicMode(enum.Enum):
    NONE = "NONE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    EDIT = "EDIT"
    FULL = "FULL"


class StudyPermissionType(enum.Enum):
    """
    User permission belongs to Study
    """

    READ = "READ"
    RUN = "RUN"
    WRITE = "WRITE"
    DELETE = "DELETE"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


@dataclass
class PermissionInfo:
    owner: Optional[int] = None
    groups: List[str] = field(default_factory=list)
    public_mode: PublicMode = PublicMode.READ


@dataclass
class PermissionFullInfo(PermissionInfo):
    permission: StudyPermissionType = StudyPermissionType.READ


@dataclass
class Event:
    type: str
    payload: Any
