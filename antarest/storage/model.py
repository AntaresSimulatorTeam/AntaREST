import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship

from antarest.common.persistence import DTO, Base


users_metadata = Table(
    "users_metadata",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("metadata_id", Integer, ForeignKey("metadata.id")),
)


class Metadata(DTO, Base):
    __tablename__ = "metadata"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True
    )
    name = Column(String(255))
    version = Column(String(255))
    author = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    users = relationship(
        "User", secondary=users_metadata, back_populates="metadata"
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
            and other.users == self.users
        )
