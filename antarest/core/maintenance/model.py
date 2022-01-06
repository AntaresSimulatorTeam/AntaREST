import uuid
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base


class MaintenanceMode(Enum):
    NORMAL = "normal_mode"
    MAINTENANCE_MODE = "maintenance_mode"
    MESSAGE_MODE = "message_mode"


class MaintenanceDTO(BaseModel):
    mode: MaintenanceMode
    message: Optional[str]


class Maintenance(Base):  # type: ignore
    __tablename__ = "maintenance"

    id = id = Column(
        String(), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    mode = Column(String, nullable=False)
    message = Column(
        String(),
    )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Maintenance):
            return False
        return bool(
            other.id == self.id
            and other.message == self.message
            and other.mode == self.mode
        )

    def __repr__(self) -> str:
        return f"id={self.id}, mode={self.mode}, message={self.message}"

    def to_dto(self) -> MaintenanceDTO:
        return MaintenanceDTO(mode=self.mode, message=self.message)
