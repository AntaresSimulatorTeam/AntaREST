from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore


class MaintenanceMode(Enum):
    NORMAL = "normal_mode"
    MAINTENANCE_MODE = "maintenance_mode"
    MESSAGE_MODE = "message_mode"


class MaintenanceDTO(BaseModel):
    mode: MaintenanceMode
    message: Optional[str]
