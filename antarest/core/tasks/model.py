import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base


class TaskStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    TIMEOUT = 5


class TaskResult(BaseModel):
    success: bool
    message: str


class TaskDTO(BaseModel):
    id: str
    name: str
    status: TaskStatus
    creation_date: DateTime
    completion_date: Optional[DateTime]
    result: Optional[TaskResult]


class TaskListFilter:
    status: Optional[TaskStatus] = TaskStatus.RUNNING
    name_regex: Optional[str] = None
    from_creation_date: Optional[DateTime] = None
    to_creation_date: Optional[DateTime] = None
    from_completion_date: Optional[DateTime] = None
    to_completion_date: Optional[DateTime] = None


class TaskJobLog(Base):  # type: ignore
    __tablename__ = "taskjoblog"

    id = Column(Integer(), primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    task_id = Column(
        String(),
        ForeignKey("taskjob.id", name="fk_log_taskjob_id"),
    )


class TaskJob(Base):  # type: ignore
    __tablename__ = "taskjob"

    id = Column(String(), default=lambda: str(uuid.uuid4()), primary_key=True)
    name = Column(String())
    status = Column(Integer(), default=lambda: TaskStatus.PENDING.value)
    creation_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime, nullable=True)
    result_msg = Column(String(), nullable=True)
    result_status = Column(Boolean(), nullable=True)
    logs = relationship(TaskJobLog, useList=True)

    def to_dto(self) -> TaskDTO:
        return TaskDTO(
            id=self.id,
            creation_date=self.creation_date,
            completion_date=self.completion_date,
            name=self.name,
            status=TaskStatus(self.status),
            result=TaskResult(
                sucess=self.result_status, message=self.result_msg
            )
            if self.completion_date
            else None,
        )
