import enum
import uuid
from pathlib import Path
from typing import Any, List

from dataclasses import dataclass
from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey, Enum, Boolean  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.common.persistence import DTO, Base
from antarest.login.model import User, Group

groups_metadata = Table(
    "group_metadata",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("metadata_id", Integer, ForeignKey("metadata.id")),
)


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Metadata(DTO, Base):  # type: ignore
    __tablename__ = "metadata"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String(255))
    version = Column(String(255))
    author = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    content_status = Column(Enum(StudyContentStatus))
    public = Column(Boolean(), default=False)
    workspace = Column(String(255), default="default")
    path = Column(String(255))
    owner_id = Column(Integer, ForeignKey(User.id))
    owner = relationship(User, uselist=False)
    groups = relationship(
        "Group", secondary=lambda: groups_metadata, cascade=""
    )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Metadata):
            return False

        return bool(
            other.id == self.id
            and other.name == self.name
            and other.version == self.version
            and other.author == self.author
            and other.created_at == self.created_at
            and other.updated_at == self.updated_at
            and other.content_status == self.content_status
            and other.public == self.public
            and other.workspace == self.workspace
            and other.path == self.path
            and other.owner == self.owner
            and other.groups == self.groups
        )

    def __str__(self) -> str:
        return f"Metadata(name={self.name}, version={self.version}, owner={self.owner}, groups={[str(u)+',' for u in self.groups]}"

    def to_json_summary(self) -> Any:
        return {"id": self.id, "name": self.name, "workspace": self.workspace}


@dataclass
class StudyFolder:
    path: Path
    workspace: str
    groups: List[Group]
