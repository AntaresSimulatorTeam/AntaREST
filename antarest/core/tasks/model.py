# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import TYPE_CHECKING, Annotated, Any, List, Optional, TypeAlias

from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    OUTPUT_VARIABLES_VIEW_MATERIALIZATION = "OUTPUT_VARIABLES_VIEW_MATERIALIZATION"


class TaskStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    TIMEOUT = 5  # Not used anymore, kept for backward compat with tasks save in database.
    CANCELLED = 6

    def is_final(self) -> bool:
        return self in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]

    @classmethod
    def parse(cls, other: object) -> "TaskStatus":
        if isinstance(other, TaskStatus):
            return other
        if isinstance(other, str):
            if other in cls.__members__:
                return cls[other]
            try:
                return cls(int(other))
            except ValueError as value_error:
                raise ValueError(f"Invalid status value : {other}") from value_error
        if isinstance(other, int):
            return cls(other)
        else:
            raise TypeError(f"Invalid status type: {type(other)!r}")


def _format_task_status(s: TaskStatus) -> str:
    return s.name


_TASK_STATUS_JSON_SCHEMA = {"type": "string", "enum": [ts.name for ts in TaskStatus]}


TaskStatusStr: TypeAlias = Annotated[
    TaskStatus,
    BeforeValidator(TaskStatus.parse),
    PlainSerializer(_format_task_status, return_type=str),
    WithJsonSchema(_TASK_STATUS_JSON_SCHEMA),
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
    status: List[TaskStatusStr] = []
    name: Optional[str] = None
    type: List[TaskType] = []
    ref_id: Optional[str] = None
    from_creation_date_utc: Optional[float] = None
    to_creation_date_utc: Optional[float] = None
    from_completion_date_utc: Optional[float] = None
    to_completion_date_utc: Optional[float] = None


class TaskJobLog(Base):
    __tablename__ = "taskjoblog"

    id: Mapped[int] = mapped_column(Integer(), Sequence("tasklog_id_sequence"), primary_key=True)
    message: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey("taskjob.id", name="fk_log_taskjob_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Define a many-to-one relationship between `TaskJobLog` and `TaskJob`.
    # If the TaskJob is deleted, all attached logs must also be deleted in cascade.
    job: Mapped["TaskJob"] = relationship("TaskJob", back_populates="logs", uselist=False)

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


class TaskJob(Base):
    __tablename__ = "taskjob"

    id: Mapped[str] = mapped_column(String(), default=lambda: str(uuid.uuid4()), primary_key=True)
    name: Mapped[str] = mapped_column(String(), nullable=False, index=True)
    status: Mapped[int] = mapped_column(Integer(), default=lambda: TaskStatus.PENDING.value, index=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    result_msg: Mapped[Optional[str]] = mapped_column(String(), nullable=True, default=None)
    result: Mapped[Optional[str]] = mapped_column(String(), nullable=True, default=None)
    result_status: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True, default=None)
    type: Mapped[Optional[str]] = mapped_column(String(), nullable=True, default=None, index=True)
    progress: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True, default=None)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer(),
        ForeignKey("identities.id", name="fk_taskjob_identity_id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    ref_id: Mapped[Optional[str]] = mapped_column(
        String(),
        ForeignKey("study.id", name="fk_taskjob_study_id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
    )

    # Define a one-to-many relationship between `TaskJob` and `TaskJobLog`.
    # If the TaskJob is deleted, all attached logs must also be deleted in cascade.
    logs: Mapped[List["TaskJobLog"]] = relationship(
        "TaskJobLog", back_populates="job", cascade="all, delete, delete-orphan"
    )

    # Define a many-to-one relationship between `TaskJob` and `Identity`.
    # If the Identity is deleted, all attached TaskJob must be preserved.
    owner: Mapped["Identity"] = relationship("Identity", back_populates="owned_jobs", uselist=False)

    # Define a many-to-one relationship between `TaskJob` and `Study`.
    # If the Study is deleted, all attached TaskJob must be deleted in cascade.
    study: Mapped["Study"] = relationship("Study", back_populates="jobs", uselist=False)

    def get_type(self) -> TaskType:
        if not self.type:
            raise ValueError("Task type is not set")
        return TaskType(self.type)

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
