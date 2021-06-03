import enum
import uuid
from pathlib import Path
from typing import Any, List

from dataclasses import dataclass
from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey, Enum, Boolean  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.common.persistence import DTO, Base
from antarest.login.model import User, Group, Identity

DEFAULT_WORKSPACE_NAME = "default"

groups_metadata = Table(
    "group_metadata",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("study_id", Integer, ForeignKey("study.id")),
)


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PublicMode(enum.Enum):
    NONE = "NONE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    EDIT = "EDIT"
    FULL = "FULL"


@dataclass
class Study(Base):  # type: ignore
    """
    Standard Study entity
    """

    __tablename__ = "study"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String(255))
    type = Column(String(50))
    version = Column(String(255))
    author = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    public_mode = Column(Enum(PublicMode), default=PublicMode.NONE)
    owner_id = Column(Integer, ForeignKey(Identity.id), nullable=True)
    owner = relationship(Identity, uselist=False)
    groups = relationship(
        "Group", secondary=lambda: groups_metadata, cascade=""
    )

    __mapper_args__ = {"polymorphic_identity": "study", "polymorphic_on": type}

    def __str__(self) -> str:
        return f"Metadata(id={self.id}, name={self.name}, version={self.version}, owner={self.owner}, groups={[str(u)+',' for u in self.groups]}"

    def to_json_summary(self) -> Any:
        return {"id": self.id, "name": self.name, "workspace": self.workspace}


@dataclass
class RawStudy(Study):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "rawstudy"

    id = Column(
        String(36),
        ForeignKey("study.id"),
        primary_key=True,
    )
    content_status = Column(Enum(StudyContentStatus))
    workspace = Column(String(255), default=DEFAULT_WORKSPACE_NAME)
    path = Column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "rawstudy",
    }


@dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: List[Group]
