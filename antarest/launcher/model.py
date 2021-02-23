import enum
from typing import Any

from sqlalchemy import Integer, Column, Enum, String  # type: ignore

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
    job_status = Column(Enum(JobStatus))
    msg = Column(String())
    exit_code = Column(Integer)

    def to_dict(self) -> JSON:
        return {
            "id": self.id,
            "status": str(self.job_status),
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
