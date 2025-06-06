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

import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, List, Mapping, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Sequence, String  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import relationship, sessionmaker  # type: ignore
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel

if TYPE_CHECKING:
    # avoid circular import
    from antarest.login.model import Identity
    from antarest.study.model import Study


class TaskType(StrEnum):
    EXPORT = "EXPORT"
    VARIANT_GENERATION = "VARIANT_GENERATION"
    COPY = "COPY"
    ARCHIVE = "ARCHIVE"
    UNARCHIVE = "UNARCHIVE"
    SCAN = "SCAN"
    UPGRADE_STUDY = "UPGRADE_STUDY"
    THERMAL_CLUSTER_SERIES_GENERATION = "THERMAL_CLUSTER_SERIES_GENERATION"
    SNAPSHOT_CLEARING = "SNAPSHOT_CLEARING"
    OUTPUT_AGGREGATION = "OUTPUT_AGGREGATION"


class TaskStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    TIMEOUT = 5
    CANCELLED = 6

    def is_final(self) -> bool:
        return self in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]


class TaskResult(AntaresBaseModel, extra="forbid"):
    success: bool
    message: str
    # Can be used to store json serialized result
    return_value: Optional[str] = None


class TaskLogDTO(AntaresBaseModel, extra="forbid"):
    id: str
    message: str


class CustomTaskEventMessages(AntaresBaseModel, extra="forbid"):
    start: str
    running: str
    end: str


class TaskEventPayload(AntaresBaseModel, extra="forbid"):
    id: str
    message: str
    type: TaskType
    study_id: Optional[str] = None


class TaskDTO(AntaresBaseModel, extra="forbid"):
    id: str
    name: str
    owner: Optional[int] = None
    status: TaskStatus
    creation_date_utc: str
    completion_date_utc: Optional[str] = None
    result: Optional[TaskResult] = None
    logs: Optional[List[TaskLogDTO]] = None
    type: Optional[str] = None
    ref_id: Optional[str] = None
    progress: Optional[int] = None


class TaskListFilter(AntaresBaseModel, extra="forbid"):
    status: List[TaskStatus] = []
    name: Optional[str] = None
    type: List[TaskType] = []
    ref_id: Optional[str] = None
    from_creation_date_utc: Optional[float] = None
    to_creation_date_utc: Optional[float] = None
    from_completion_date_utc: Optional[float] = None
    to_completion_date_utc: Optional[float] = None


class TaskJobLog(Base):  # type: ignore
    __tablename__ = "taskjoblog"

    id = Column(Integer(), Sequence("tasklog_id_sequence"), primary_key=True)
    message = Column(String, nullable=False)
    task_id = Column(
        String(),
        ForeignKey("taskjob.id", name="fk_log_taskjob_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Define a many-to-one relationship between `TaskJobLog` and `TaskJob`.
    # If the TaskJob is deleted, all attached logs must also be deleted in cascade.
    job: "TaskJob" = relationship("TaskJob", back_populates="logs", uselist=False)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TaskJobLog):
            return False
        return bool(other.id == self.id and other.message == self.message and other.task_id == self.task_id)

    @override
    def __repr__(self) -> str:
        return f"id={self.id}, message={self.message}, task_id={self.task_id}"

    def to_dto(self) -> TaskLogDTO:
        return TaskLogDTO(id=self.id, message=self.message)


class TaskJob(Base):  # type: ignore
    __tablename__ = "taskjob"

    id: str = Column(String(), default=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Column(String(), nullable=False, index=True)
    status: int = Column(Integer(), default=lambda: TaskStatus.PENDING.value, index=True)
    creation_date: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    completion_date: Optional[datetime] = Column(DateTime, nullable=True, default=None)
    result_msg: Optional[str] = Column(String(), nullable=True, default=None)
    result: Optional[str] = Column(String(), nullable=True, default=None)
    result_status: Optional[bool] = Column(Boolean(), nullable=True, default=None)
    type: Optional[str] = Column(String(), nullable=True, default=None, index=True)
    progress: Optional[int] = Column(Integer(), nullable=True, default=None)
    owner_id: int = Column(
        Integer(),
        ForeignKey("identities.id", name="fk_taskjob_identity_id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    ref_id: Optional[str] = Column(
        String(),
        ForeignKey("study.id", name="fk_taskjob_study_id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
    )

    # Define a one-to-many relationship between `TaskJob` and `TaskJobLog`.
    # If the TaskJob is deleted, all attached logs must also be deleted in cascade.
    logs: List["TaskJobLog"] = relationship("TaskJobLog", back_populates="job", cascade="all, delete, delete-orphan")

    # Define a many-to-one relationship between `TaskJob` and `Identity`.
    # If the Identity is deleted, all attached TaskJob must be preserved.
    owner: "Identity" = relationship("Identity", back_populates="owned_jobs", uselist=False)

    # Define a many-to-one relationship between `TaskJob` and `Study`.
    # If the Study is deleted, all attached TaskJob must be deleted in cascade.
    study: "Study" = relationship("Study", back_populates="jobs", uselist=False)

    def to_dto(self, with_logs: bool = False) -> TaskDTO:
        result = None
        if self.completion_date:
            assert self.result_status is not None
            assert self.result_msg is not None
            result = TaskResult(
                success=self.result_status,
                message=self.result_msg,
                return_value=self.result,
            )
        return TaskDTO(
            id=self.id,
            owner=self.owner_id,
            creation_date_utc=str(self.creation_date),
            completion_date_utc=str(self.completion_date) if self.completion_date else None,
            name=self.name,
            status=TaskStatus(self.status),
            result=result,
            logs=sorted([log.to_dto() for log in self.logs], key=lambda log: log.id) if with_logs else None,
            type=self.type,
            ref_id=self.ref_id,
            progress=self.progress,
        )

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TaskJob):
            return False
        return bool(
            other.id == self.id
            and other.owner_id == self.owner_id
            and other.creation_date == self.creation_date
            and other.completion_date == self.completion_date
            and other.name == self.name
            and other.status == self.status
            and other.result_msg == self.result_msg
            and other.result_status == self.result_status
            and other.logs == self.logs
        )

    @override
    def __repr__(self) -> str:
        return (
            f"id={self.id},"
            f" logs={self.logs},"
            f" owner_id={self.owner_id},"
            f" creation_date={self.creation_date},"
            f" completion_date={self.completion_date},"
            f" name={self.name},"
            f" status={self.status},"
            f" result_msg={self.result_msg},"
            f" result_status={self.result_status}"
        )


def cancel_orphan_tasks(engine: Engine, session_args: Mapping[str, bool]) -> None:
    """
    Cancel all tasks that are currently running or pending.

    When the web application restarts, such as after a new deployment, any pending or running tasks may be lost.
    To mitigate this, it is preferable to set these tasks to a "FAILED" status.
    This ensures that users can easily identify the tasks that were affected by the restart and take appropriate
    actions, such as restarting the tasks manually.

    Args:
        engine: The database engine (SQLAlchemy connection to SQLite or PostgreSQL).
        session_args: The session arguments (SQLAlchemy session arguments).
    """
    updated_values = {
        TaskJob.status: TaskStatus.FAILED.value,
        TaskJob.result_status: False,
        TaskJob.result_msg: "Task was interrupted due to server restart",
        TaskJob.completion_date: datetime.utcnow(),
    }
    orphan_status = [TaskStatus.RUNNING.value, TaskStatus.PENDING.value]
    make_session = sessionmaker(bind=engine, **session_args)
    with make_session() as session:
        q = session.query(TaskJob).filter(TaskJob.status.in_(orphan_status))  # type: ignore
        q.update(updated_values, synchronize_session=False)
        session.commit()
