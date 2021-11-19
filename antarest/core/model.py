import enum
from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel

JSON = Dict[str, Any]
ELEMENT = Union[str, int, float, bool, bytes]
SUB_JSON = Union[ELEMENT, JSON, List, None]


class PublicMode(str, enum.Enum):
    NONE = "NONE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    EDIT = "EDIT"
    FULL = "FULL"


class StudyPermissionType(str, enum.Enum):
    """
    User permission belongs to Study
    """

    READ = "READ"
    RUN = "RUN"
    WRITE = "WRITE"
    DELETE = "DELETE"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


class PermissionInfo(BaseModel):
    owner: Optional[int] = None
    groups: List[str] = list()
    public_mode: PublicMode = PublicMode.NONE
