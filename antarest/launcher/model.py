import enum

from dataclasses import dataclass
from sqlalchemy import Integer, Column, Enum, String, Sequence

from antarest.common.custom_types import JSON
from antarest.common.persistence import Base


class JobStatus(enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


class JobResult(Base):  # type: ignore
    __tablename__ = "job_result"

    id = Column(Integer, Sequence("job_id_sed"), primary_key=True)
    job_status = Column(Enum(JobStatus))
    msg = Column(String())
    exit_code = Column(Integer)

    def to_dict(self) -> JSON:
        return {
            "status": str(self.job_status),
            "msg": self.msg,
            "exit_code": self.exit_code,
        }
