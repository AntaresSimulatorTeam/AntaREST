import enum
from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel
from sqlalchemy import Integer, Column, Enum, String, DateTime  # type: ignore

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

    def to_dto(self) -> JobResultDTO:
        return JobResultDTO(
            id=self.id,
            study_id=self.study_id,
            launcher=self.launcher,
            status=self.job_status,
            creation_date=str(self.creation_date),
            completion_date=str(self.completion_date),
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
