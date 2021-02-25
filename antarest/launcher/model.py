import enum
from datetime import datetime
from typing import Any

from sqlalchemy import Integer, Column, Enum, String, DateTime  # type: ignore

from antarest.common.custom_types import JSON
from antarest.common.persistence import Base, DTO


class JobStatus(enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


class JobResult(DTO, Base):  # type: ignore
    __tablename__ = "job_result"
    id = Column(String(36), primary_key=True)
    study_id = Column(String(36))
    job_status = Column(Enum(JobStatus))
    creation_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    msg = Column(String())
    exit_code = Column(Integer)

    def to_dict(self) -> JSON:
        return {
            "id": self.id,
            "study_id": self.study_id,
            "status": str(self.job_status),
            "creation_date": str(self.creation_date),
            "completion_date": str(self.completion_date),
            "msg": self.msg,
            "exit_code": self.exit_code,
        }

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, JobResult):
            return False
        return o.to_dict() == self.to_dict()

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return self.__str__()
