import enum
import uuid
from typing import Any

from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey, Enum  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.common.persistence import DTO, Base

users_metadata = Table(
    "users_metadata",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
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
    users = relationship("User", secondary=lambda: users_metadata, cascade="")

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
            and other.users == self.users
        )

    def __str__(self) -> str:
        return f"Metadata(name={self.name}, version={self.version}, users={[str(u)+',' for u in self.users]}"
