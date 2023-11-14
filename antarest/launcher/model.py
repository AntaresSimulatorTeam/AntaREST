import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Sequence, String  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.login.model import Identity


class XpansionParametersDTO(BaseModel):
    output_id: Optional[str]
    sensitivity_mode: bool = False
    enabled: bool = True


class LauncherParametersDTO(BaseModel):
    # Warning ! This class must be retro-compatible (that's the reason for the weird bool/XpansionParametersDTO union)
    # The reason is that it's stored in json format in database and deserialized using the latest class version
    # If compatibility is to be broken, an (alembic) data migration script should be added
    adequacy_patch: Optional[Dict[str, Any]] = None
    nb_cpu: Optional[int] = None
    post_processing: bool = False
    time_limit: Optional[int] = None  # 3600 ≤ time_limit < 864000 (10 days)
    xpansion: Union[XpansionParametersDTO, bool, None] = None
    xpansion_r_version: bool = False
    archive_output: bool = True
    auto_unzip: bool = True
    output_suffix: Optional[str] = None
    other_options: Optional[str] = None
    # add extensions field here


class LogType(str, enum.Enum):
    STDOUT = "STDOUT"
    STDERR = "STDERR"

    @staticmethod
    def from_filename(filename: str) -> Optional["LogType"]:
        if filename == "antares-err.log":
            return LogType.STDERR
        elif filename == "antares-out.log":
            return LogType.STDOUT
        else:
            return None

    def to_suffix(self) -> str:
        if self == LogType.STDOUT:
            return "out.log"
        elif self == LogType.STDERR:
            return "err.log"
        else:  # pragma: no cover
            return "out.log"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


class JobLogType(str, enum.Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class JobResultDTO(BaseModel):
    """
    A data transfer object (DTO) representing the job result.

    - id: The unique identifier for the task (UUID).
    - study_id: The unique identifier for the Antares study (UUID).
    - launcher: The name of the launcher for a simulation task, with possible values "local", "slurm" or `None`.
    - launcher_params: Parameters related to the launcher.
    - status: The status of the task. It can be one of the following: "pending", "failed", "success", or "running".
    - creation_date: The date of creation of the task.
    - completion_date: The date of completion of the task, if available.
    - msg: A message associated with the task, either for the user or for error description.
    - output_id: The identifier of the simulation results.
    - exit_code: The exit code associated with the task.
    - solver_stats: Global statistics related to the simulation, including processing time,
      call count, optimization issues, and study-specific statistics (INI file-like format).
    - owner_id: The unique identifier of the user or bot that executed the task.
    """

    id: str
    study_id: str
    launcher: Optional[str]
    launcher_params: Optional[str]
    status: JobStatus
    creation_date: str
    completion_date: Optional[str]
    msg: Optional[str]
    output_id: Optional[str]
    exit_code: Optional[int]
    solver_stats: Optional[str]
    owner_id: Optional[int]


class JobLog(Base):  # type: ignore
    __tablename__ = "launcherjoblog"

    id: str = Column(Integer(), Sequence("launcherjoblog_id_sequence"), primary_key=True)
    message: str = Column(String, nullable=False)
    job_id: str = Column(
        String(),
        ForeignKey("job_result.id", name="fk_log_job_result_id"),
    )
    log_type: str = Column(String, nullable=False)

    # SQLAlchemy provides its own way to handle object comparison, which ensures
    # that the comparison is based on the database identity of the objects.
    # So, implementing `__eq__` and `__ne__` is not necessary.

    def __str__(self) -> str:
        return f"Job log #{self.id} {self.log_type}: '{self.message}'"

    def __repr__(self) -> str:
        return (
            f"<JobLog(id={self.id!r},"
            f" message={self.message!r},"
            f" job_id={self.job_id!r},"
            f" log_type={self.log_type!r})>"
        )


class JobResult(Base):  # type: ignore
    __tablename__ = "job_result"

    id: str = Column(String(36), primary_key=True)
    study_id: str = Column(String(36))
    launcher: Optional[str] = Column(String)
    launcher_params: Optional[str] = Column(String, nullable=True)
    job_status: JobStatus = Column(Enum(JobStatus))
    creation_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    msg: Optional[str] = Column(String())
    output_id: Optional[str] = Column(String())
    exit_code: Optional[int] = Column(Integer)
    solver_stats: Optional[str] = Column(String(), nullable=True)
    owner_id: Optional[int] = Column(Integer(), ForeignKey(Identity.id, ondelete="SET NULL"), nullable=True)

    logs = relationship(JobLog, uselist=True, cascade="all, delete, delete-orphan")

    def to_dto(self) -> JobResultDTO:
        return JobResultDTO(
            id=self.id,
            study_id=self.study_id,
            launcher=self.launcher,
            launcher_params=self.launcher_params,
            status=self.job_status,
            creation_date=str(self.creation_date),
            completion_date=str(self.completion_date) if self.completion_date else None,
            msg=self.msg,
            output_id=self.output_id,
            exit_code=self.exit_code,
            solver_stats=self.solver_stats,
            owner_id=self.owner_id,
        )

    # SQLAlchemy provides its own way to handle object comparison, which ensures
    # that the comparison is based on the database identity of the objects.
    # So, implementing `__eq__` and `__ne__` is not necessary.

    def __str__(self) -> str:
        return f"Job result #{self.id} (study '{self.study_id}'): {self.job_status}"

    def __repr__(self) -> str:
        return (
            f"<JobResult(id={self.id!r},"
            f" study_id={self.study_id!r},"
            f" launcher={self.launcher!r},"
            f" launcher_params={self.launcher_params!r},"
            f" job_status={self.job_status!r},"
            f" creation_date={self.creation_date!r},"
            f" completion_date={self.completion_date!r},"
            f" msg={self.msg!r},"
            f" output_id={self.output_id!r},"
            f" exit_code={self.exit_code!r},"
            f" solver_stats={self.solver_stats!r},"
            f" owner_id={self.owner_id!r})>"
        )


class JobCreationDTO(BaseModel):
    job_id: str


class LauncherEnginesDTO(BaseModel):
    engines: List[str]
