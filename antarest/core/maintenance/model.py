from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore


class MaintenanceMode(str, Enum):
    NORMAL_MODE = "NORMAL"
    MAINTENANCE_MODE = "MAINTENANCE"

    @staticmethod
    def to_str(element: bool) -> str:
        if element:
            return MaintenanceMode.MAINTENANCE_MODE.value
        return MaintenanceMode.NORMAL_MODE.value
