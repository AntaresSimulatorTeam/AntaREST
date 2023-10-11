from enum import Enum
from typing import Set

from pydantic import BaseModel


class BindingConstraintFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintDTO(BaseModel):
    id: str
    areas: Set[str]
    clusters: Set[str]
    time_step: BindingConstraintFrequency
