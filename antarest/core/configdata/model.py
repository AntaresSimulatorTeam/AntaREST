import uuid
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base


class ConfigDataDTO(BaseModel):
    key: str
    value: Optional[str]


class ConfigData(Base):  # type: ignore
    __tablename__ = "configdata"

    key = Column(String(), default=lambda: str(uuid.uuid4()), primary_key=True)
    value = Column(String, nullable=True)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConfigData):
            return False
        return bool(other.key == self.key and other.value == self.value)

    def __repr__(self) -> str:
        return f"key={self.key}, value={self.value}"

    def to_dto(self) -> ConfigDataDTO:
        return ConfigDataDTO(key=self.key, value=self.value)


# APP MAIN CONFIG KEYS
class ConfigDataAppKeys(Enum):
    MAINTENANCE_MODE = "maintenance_mode"
    MAINTENANCE_MESSAGE = "maintenance_message"
