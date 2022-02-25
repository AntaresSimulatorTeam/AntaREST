import enum
from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel
from sqlalchemy import Integer, Column, Enum, String, DateTime, Sequence, ForeignKey  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.core.utils.utils import DTO


class LogType(str, enum.Enum):
    STDOUT = "STDOUT"
    STDERR = "STDERR"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


class JobLogType(str, enum.Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class JobResultDTO(BaseModel):
    id: str
    study_id: str
    launcher: Optional[str]
    status: JobStatus
    creation_date: str
    completion_date: Optional[str]
    msg: Optional[str]
    output_id: Optional[str]
    exit_code: Optional[int]


class JobLog(DTO, Base):  # type: ignore
    __tablename__ = "launcherjoblog"

    id = Column(
        Integer(), Sequence("launcherjoblog_id_sequence"), primary_key=True
    )
    message = Column(String, nullable=False)
    job_id = Column(
        String(),
        ForeignKey("job_result.id", name="fk_log_job_result_id"),
    )
    log_type = Column(String, nullable=False)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, JobLog):
            return False
        return bool(
            other.id == self.id
            and other.message == self.message
            and other.log_type == self.log_type
            and other.job_id == self.job_id
        )

    def __repr__(self) -> str:
        return f"id={self.id}, message={self.message}, log_type={self.log_type}, job_id={self.job_id}"


class JobResult(DTO, Base):  # type: ignore
    __tablename__ = "job_result"

    id = Column(String(36), primary_key=True)
    study_id = Column(String(36))
    launcher = Column(String)
    job_status = Column(Enum(JobStatus))
    creation_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    msg = Column(String())
    output_id = Column(String())
    exit_code = Column(Integer)
    logs = relationship(
        JobLog, uselist=True, cascade="all, delete, delete-orphan"
    )

    def to_dto(self) -> JobResultDTO:
        return JobResultDTO(
            id=self.id,
            study_id=self.study_id,
            launcher=self.launcher,
            status=self.job_status,
            creation_date=str(self.creation_date),
            completion_date=str(self.completion_date)
            if self.completion_date
            else None,
            msg=self.msg,
            output_id=self.output_id,
            exit_code=self.exit_code,
        )

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, JobResult):
            return False
        return o.to_dto().dict() == self.to_dto().dict()

    def __str__(self) -> str:
        return str(self.to_dto().dict())

    def __repr__(self) -> str:
        return self.__str__()


class JobCreationDTO(BaseModel):
    job_id: str


class LauncherEnginesDTO(BaseModel):
    engines: List[str]
