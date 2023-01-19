import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import BaseModel

if TYPE_CHECKING:
    # These dependencies are only used for type checking with mypy.
    from antarest.study.model import Study, StudyMetadataDTO

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
    groups: List[str] = []
    public_mode: PublicMode = PublicMode.NONE

    @classmethod
    def from_study(
        cls, study: Union["Study", "StudyMetadataDTO"]
    ) -> "PermissionInfo":
        return cls(
            owner=None if study.owner is None else study.owner.id,
            groups=[g.id for g in study.groups if g.id is not None],
            public_mode=PublicMode.NONE
            if study.public_mode is None
            else PublicMode(study.public_mode),
        )
