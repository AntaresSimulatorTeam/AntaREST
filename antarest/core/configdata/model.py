from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String  # type: ignore

from antarest.core.persistence import Base


class ConfigDataDTO(BaseModel):
    key: str
    value: Optional[str]


class ConfigData(Base):  # type: ignore
    __tablename__ = "configdata"
    owner = Column(Integer(), primary_key=True)
    key = Column(String(), primary_key=True)
    value = Column(String(), nullable=True)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConfigData):
            return False
        return bool(other.key == self.key and other.value == self.value and other.owner == self.owner)

    def __repr__(self) -> str:
        return f"key={self.key}, value={self.value}, owner={self.owner}"

    def to_dto(self) -> ConfigDataDTO:
        return ConfigDataDTO(key=self.key, value=self.value)


# APP MAIN CONFIG KEYS
class ConfigDataAppKeys(str, Enum):
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    MESSAGE_INFO = "MESSAGE_INFO"
