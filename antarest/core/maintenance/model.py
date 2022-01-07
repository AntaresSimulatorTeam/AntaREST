from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore


class MaintenanceMode(str, Enum):
    NORMAL_MODE = "normal_mode"
    MAINTENANCE_MODE = "maintenance_mode"

    @staticmethod
    def from_str(element):
        if element == "normal_mode":
            return MaintenanceMode.NORMAL_MODE
        elif element == "maintenance_mode":
            return MaintenanceMode.MAINTENANCE_MODE
        else:
            raise NotImplementedError
