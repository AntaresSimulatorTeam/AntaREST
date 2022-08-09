import enum
from typing import Any, Dict

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Enum  # type: ignore


class ScheduledActionDTO(BaseModel):
    name: str
    args: Dict[str, Any]


class ScheduledActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class ScheduledAction(Base):  # type: ignore
    __tablename__ = "scheduled_actions"

    id = Column(String(64), primary_key=True)
    name = Column(String())
    status = Column(
        Enum(ScheduledActionStatus), default=ScheduledActionStatus.PENDING
    )
    # this would be a task result
    completion_result = Column(String(), nullable=True)
    scheduled_date = Column(DateTime)
    created_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
