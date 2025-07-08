# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import enum
import typing
from datetime import datetime
from typing import Any, Dict, List, MutableMapping, Optional
from uuid import uuid4

from pydantic import Field
from pydantic.alias_generators import to_camel
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.login.model import Identity, UserInfo


class XpansionParametersDTO(AntaresBaseModel):
    output_id: Optional[str] = None
    sensitivity_mode: bool = False
    enabled: bool = True


class LauncherParametersDTO(AntaresBaseModel):
    # Warning ! This class must be retro-compatible (that's the reason for the weird bool/XpansionParametersDTO union)
    # The reason is that it's stored in json format in database and deserialized using the latest class version
    # If compatibility is to be broken, an (alembic) data migration script should be added
    adequacy_patch: Optional[Dict[str, Any]] = None
    nb_cpu: Optional[int] = None
    post_processing: bool = False
    time_limit: int = 240 * 3600  # Default value set to 240 hours (in seconds)
    xpansion: XpansionParametersDTO | bool | None = None
    xpansion_r_version: bool = False
    archive_output: bool = True
    auto_unzip: bool = True
    output_suffix: Optional[str] = None
    other_options: Optional[str] = None
    launcher_id: Optional[str] = None

    # add extensions field here

    @classmethod
    def from_launcher_params(cls, params: Optional[str]) -> "LauncherParametersDTO":
        """
        Convert the launcher parameters from a string to a `LauncherParametersDTO` object.
        """
        if params is None:
            return cls()
        return cls.model_validate(from_json(params))


class LogType(enum.StrEnum):
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


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


class JobLogType(enum.StrEnum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class JobResultDTO(AntaresBaseModel):
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
    - owner: The user or bot that executed the task or `None` if unknown.
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
    owner: Optional[UserInfo]

    class Config:
        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = JobResultDTO(
                id="b2a9f6a7-7f8f-4f7a-9a8b-1f9b4c5d6e7f",
                study_id="b2a9f6a7-7f8f-4f7a-9a8b-1f9b4c5d6e7f",
                launcher="slurm",
                launcher_params='{"nb_cpu": 4, "time_limit": 3600}',
                status=JobStatus.SUCCESS,
                creation_date="2023-11-25 12:00:00",
                completion_date="2023-11-25 12:27:31",
                msg="Study successfully executed",
                output_id="20231125-1227eco",
                exit_code=0,
                solver_stats="time: 1651s, call_count: 1, optimization_issues: []",
                owner=UserInfo(id=0o007, name="James BOND"),
            ).model_dump(mode="json")


class JobLog(Base):  # type: ignore
    __tablename__ = "launcherjoblog"

    id: int = Column(Integer(), Sequence("launcherjoblog_id_sequence"), primary_key=True)
    message: str = Column(String, nullable=False)
    job_id: str = Column(
        String(),
        ForeignKey("job_result.id", name="fk_log_job_result_id"),
    )
    log_type: str = Column(String, nullable=False)

    # SQLAlchemy provides its own way to handle object comparison, which ensures
    # that the comparison is based on the database identity of the objects.
    # So, implementing `__eq__` and `__ne__` is not necessary.

    @override
    def __str__(self) -> str:
        return f"Job log #{self.id} {self.log_type}: '{self.message}'"

    @override
    def __repr__(self) -> str:
        return f"<JobLog(id={self.id!r}, message={self.message!r}, job_id={self.job_id!r}, log_type={self.log_type!r})>"


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

    # Define a many-to-one relationship between `JobResult` and `Identity`.
    # This relationship is required to display the owner of a job result in the UI.
    # If the owner is deleted, the job result is detached from the owner (but not deleted).
    owner: Optional[Identity] = relationship(Identity, back_populates="job_results", uselist=False)

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
            owner=self.owner.to_dto() if self.owner else None,
        )

    # SQLAlchemy provides its own way to handle object comparison, which ensures
    # that the comparison is based on the database identity of the objects.
    # So, implementing `__eq__` and `__ne__` is not necessary.

    @override
    def __str__(self) -> str:
        return f"Job result #{self.id} (study '{self.study_id}'): {self.job_status}"

    @override
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

    def copy_jobs_for_study(self, study_id: str) -> typing.Self:
        data = {
            column.key: getattr(self, column.key)
            for column in self.__table__.columns
            if column.key not in ["id", "study_id"]
        }
        return JobResult(
            **data,
            id=str(uuid4()),
            study_id=study_id,
        )


class JobCreationDTO(AntaresBaseModel):
    job_id: str


class LauncherEnginesDTO(AntaresBaseModel):
    engines: List[str]


class LauncherLoadDTO(AntaresBaseModel, extra="forbid", alias_generator=to_camel):
    """
    DTO representing the load of the SLURM cluster or local machine.

    Attributes:
        allocated_cpu_rate: The rate of allocated CPU, in range (0, 100).
        cluster_load_rate: The rate of cluster load, in range (0, 100).
        nb_queued_jobs: The number of queued jobs.
        launcher_status: The status of the launcher: "SUCCESS" or "FAILED".
    """

    allocated_cpu_rate: float = Field(
        description="The rate of allocated CPU, in range (0, 100)",
        ge=0,
        le=100,
        title="Allocated CPU Rate",
    )
    cluster_load_rate: float = Field(
        description="The rate of cluster load, in range (0, 100)",
        ge=0,
        le=100,
        title="Cluster Load Rate",
    )
    nb_queued_jobs: int = Field(
        description="The number of queued jobs",
        ge=0,
        title="Number of Queued Jobs",
    )
    launcher_status: str = Field(
        description="The status of the launcher: 'SUCCESS' or 'FAILED'",
        title="Launcher Status",
    )
