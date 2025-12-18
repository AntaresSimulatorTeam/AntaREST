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
import json
import re
import typing
from datetime import datetime
from typing import Annotated, Any, Dict, List, MutableMapping, Optional, TypeAlias
from uuid import uuid4

from antares.study.version import SolverVersion
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.login.model import Identity, UserInfo
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName

SolverParams = Dict[str, str]


def _format_solver_version(v: SolverVersion) -> str:
    return f"{v:2d}"


SolverVersionStr: TypeAlias = Annotated[
    SolverVersion, BeforeValidator(SolverVersion.parse), PlainSerializer(_format_solver_version, return_type=str)
]

ALLOWED_SOLVER_PRESETS_PARAM_PATTERN = re.compile(
    r"^[a-zA-Z0-9_]+$|^\d+\.\d+$"
)  # alphanumeric, underscore, or decimal number
MIN_SOLVER_PRESETS_FOR_OPTIM_PARAMS = STUDY_VERSION_9_2


class XpansionParametersDTO(AntaresBaseModel, extra="forbid"):
    output_id: Optional[str] = None
    sensitivity_mode: bool = False
    enabled: bool = True
    adequacy_criterion: bool = False

    @model_validator(mode="after")
    def check_coherence(self) -> "XpansionParametersDTO":
        if self.sensitivity_mode and self.adequacy_criterion:
            raise ValueError("Cannot launch a sensitivity analysis and an adequacy criterion one at the same time")
        return self


class LauncherParametersDTO(AntaresBaseModel, extra="forbid"):
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

    @staticmethod
    def model_config_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
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

    model_config = ConfigDict(json_schema_extra=model_config_json_schema_extra)


class JobLog(Base):
    __tablename__ = "launcherjoblog"

    id: Mapped[int] = mapped_column(Integer(), Sequence("launcherjoblog_id_sequence"), primary_key=True)
    message: Mapped[str] = mapped_column(String, nullable=False)
    job_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey("job_result.id", name="fk_log_job_result_id"),
    )
    log_type: Mapped[str] = mapped_column(String, nullable=False)

    # SQLAlchemy provides its own way to handle object comparison, which ensures
    # that the comparison is based on the database identity of the objects.
    # So, implementing `__eq__` and `__ne__` is not necessary.

    @override
    def __str__(self) -> str:
        return f"Job log #{self.id} {self.log_type}: '{self.message}'"

    @override
    def __repr__(self) -> str:
        return f"<JobLog(id={self.id!r}, message={self.message!r}, job_id={self.job_id!r}, log_type={self.log_type!r})>"


class JobResult(Base):
    __tablename__ = "job_result"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(36))
    launcher: Mapped[Optional[str]] = mapped_column(String)
    launcher_params: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    job_status: Mapped[Optional[JobStatus]] = mapped_column(Enum(JobStatus), nullable=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(String())
    output_id: Mapped[Optional[str]] = mapped_column(String())
    exit_code: Mapped[Optional[int]] = mapped_column(Integer)
    solver_stats: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer(), ForeignKey(Identity.id, ondelete="SET NULL"), nullable=True
    )

    # Define a many-to-one relationship between `JobResult` and `Identity`.
    # This relationship is required to display the owner of a job result in the UI.
    # If the owner is deleted, the job result is detached from the owner (but not deleted).
    owner: Mapped[Optional[Identity]] = relationship(Identity, back_populates="job_results", uselist=False)

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
        return type(self)(
            **data,
            id=str(uuid4()),
            study_id=study_id,
        )


class JobCreationDTO(AntaresBaseModel):
    job_id: str


class LauncherResourceRangeDTO(AntaresBaseModel, extra="forbid"):
    min: int
    max: int
    default: int


class LauncherInfoDTO(AntaresBaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    name: str
    nb_cores: LauncherResourceRangeDTO
    time_limit: LauncherResourceRangeDTO
    versions: list[SolverVersionStr]


class LauncherListDTO(AntaresBaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )

    launchers: List[LauncherInfoDTO]
    default_launcher: str


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


class SolverPresets(AntaresBaseModel):
    @staticmethod
    def model_config_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
        schema["example"] = SolverPresets(
            id="preset-001",
            name="xpress-fast",
            linear_solver="xpress",
            min_antares_version=SolverVersion.parse("9.2"),
            max_antares_version=None,
            linear_solver_param_optim_1={"THREADS": "4", "PRESOLVE": "1"},
            linear_solver_param_optim_2={"MIPRELSTOP": "0.01"},
            linear_solver_param={"MAXTIME": "3600"},
            use_optim_1_basis_next_week=True,
            use_optim_1_basis_optim_2=True,
        ).model_dump(mode="json", by_alias=True)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra=model_config_json_schema_extra,
    )

    id: str
    name: ItemName
    linear_solver: str
    min_antares_version: Optional[SolverVersionStr] = None
    max_antares_version: Optional[SolverVersionStr] = None
    linear_solver_param_optim_1: Optional[SolverParams] = None
    linear_solver_param_optim_2: Optional[SolverParams] = None
    linear_solver_param: Optional[SolverParams] = None
    use_optim_1_basis_next_week: bool = True
    use_optim_1_basis_optim_2: bool = True

    @field_validator(
        "linear_solver_param",
        "linear_solver_param_optim_1",
        "linear_solver_param_optim_2",
    )
    def validate_solver_params(cls, sp: Optional[SolverParams]) -> Optional[SolverParams]:
        if not sp:
            return sp
        for k, v in sp.items():
            if not ALLOWED_SOLVER_PRESETS_PARAM_PATTERN.match(k):
                raise ValueError(
                    f"Invalid key '{k}' in solver params. Allowed: letters, digits, underscores, and decimal points."
                )
            if not ALLOWED_SOLVER_PRESETS_PARAM_PATTERN.match(v):
                raise ValueError(
                    f"Invalid value '{v}' for key '{k}' in solver params. Allowed: letters, digits, underscores, and decimal points."
                )
        return sp

    @model_validator(mode="after")
    def validate_versions_and_optim_params(self) -> "SolverPresets":
        # min <= max
        if self.min_antares_version and self.max_antares_version:
            if self.min_antares_version > self.max_antares_version:
                raise ValueError("min_antares_version cannot be greater than max_antares_version")

        is_min_version_9_2 = (
            self.min_antares_version is not None and self.min_antares_version >= MIN_SOLVER_PRESETS_FOR_OPTIM_PARAMS
        )

        # linear_solver_param_optim_* only valid for >= 9.2
        if self.linear_solver_param_optim_1 and not is_min_version_9_2:
            raise ValueError(
                "linear_solver_param_optim_1 is not supported before Antares version 9.2 "
                f"(got {self.min_antares_version})"
            )

        if self.linear_solver_param_optim_2 and not is_min_version_9_2:
            raise ValueError(
                "linear_solver_param_optim_2 is not supported before Antares version 9.2 "
                f"(got {self.min_antares_version})"
            )

        return self

    def to_cli_options(self) -> str:
        """
        Generate an 'cli_options' string. This will be passed to the antares launcher script.

        This represents the solver presets in a command-line format.

        Example output:
            xpress nobasis1 param-optim1="THREADS 4 PRESOLVE 1" param-optim2="MIPRELSTOP 0.01"
        """
        options: list[str] = [self.linear_solver.lower()]

        if not self.use_optim_1_basis_next_week:
            options.append("nobasis1")
        if not self.use_optim_1_basis_optim_2:
            options.append("nobasis2")

        # Build per-optim strings
        def build_param_str(param_list: Dict[str, str]) -> str:
            return " ".join(f"{k} {v}" for k, v in param_list.items())

        # param-optim1
        param1 = build_param_str(self.linear_solver_param_optim_1 or {})
        param_common = build_param_str(self.linear_solver_param or {})
        combined1 = f"{param_common} {param1}".strip()
        if combined1:
            options.append(f'param-optim1="{combined1}"')

        # param-optim2
        param2 = build_param_str(self.linear_solver_param_optim_2 or {})
        combined2 = f"{param_common} {param2}".strip()
        if combined2:
            options.append(f'param-optim2="{combined2}"')

        return " ".join(options)


class SolverPresetsCreation(AntaresBaseModel):
    @staticmethod
    def model_config_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
        schema["example"] = SolverPresetsCreation(
            name="xpress-fast",
            linear_solver="xpress",
            min_antares_version=SolverVersion.parse("9.2"),
            max_antares_version=None,
            linear_solver_param_optim_1={"THREADS": "4", "PRESOLVE": "1"},
            linear_solver_param_optim_2={"MIPRELSTOP": "0.01"},
            linear_solver_param={"MAXTIME": "3600"},
            use_optim_1_basis_next_week=True,
            use_optim_1_basis_optim_2=True,
        ).model_dump(mode="json", by_alias=True)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra=model_config_json_schema_extra,
    )

    name: ItemName
    linear_solver: str
    min_antares_version: Optional[SolverVersionStr] = None
    max_antares_version: Optional[SolverVersionStr] = None
    linear_solver_param_optim_1: Optional[SolverParams] = None
    linear_solver_param_optim_2: Optional[SolverParams] = None
    linear_solver_param: Optional[SolverParams] = None
    use_optim_1_basis_next_week: Optional[bool] = None
    use_optim_1_basis_optim_2: Optional[bool] = None


class SolverPresetsUpdate(AntaresBaseModel):
    @staticmethod
    def model_config_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
        schema["example"] = SolverPresetsUpdate(
            linear_solver="xpress",
            min_antares_version=SolverVersion.parse("9.2"),
            max_antares_version=None,
            linear_solver_param_optim_1={"THREADS": "4", "PRESOLVE": "1"},
            linear_solver_param_optim_2={"MIPRELSTOP": "0.01"},
            linear_solver_param={"MAXTIME": "3600"},
            use_optim_1_basis_next_week=True,
            use_optim_1_basis_optim_2=True,
        ).model_dump(mode="json", by_alias=True)

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra=model_config_json_schema_extra,
    )

    linear_solver: Optional[str] = None
    min_antares_version: Optional[SolverVersionStr] = None
    max_antares_version: Optional[SolverVersionStr] = None
    linear_solver_param_optim_1: Optional[SolverParams] = None
    linear_solver_param_optim_2: Optional[SolverParams] = None
    linear_solver_param: Optional[SolverParams] = None
    use_optim_1_basis_next_week: Optional[bool] = None
    use_optim_1_basis_optim_2: Optional[bool] = None


class SolverPresetsDB(Base):
    __tablename__ = "solver_presets"

    id = mapped_column(String(36), primary_key=True)
    name = mapped_column(String)
    linear_solver = mapped_column(String)
    min_antares_version = mapped_column(String, nullable=True)
    max_antares_version = mapped_column(String, nullable=True)
    linear_solver_param_optim_1 = mapped_column(String, nullable=True)
    linear_solver_param_optim_2 = mapped_column(String, nullable=True)
    linear_solver_param = mapped_column(String, nullable=True)
    use_optim_1_basis_next_week = mapped_column(Boolean)
    use_optim_1_basis_optim_2 = mapped_column(Boolean)

    def to_model(self) -> SolverPresets:
        min_version = None
        if self.min_antares_version is not None:
            try:
                min_version = SolverVersion.parse(self.min_antares_version)
            except Exception as e:
                raise ValueError(f"Failed to parse min_antares_version '{self.min_antares_version}': {e}") from e

        max_version = None
        if self.max_antares_version is not None:
            try:
                max_version = SolverVersion.parse(self.max_antares_version)
            except Exception as e:
                raise ValueError(f"Failed to parse max_antares_version '{self.max_antares_version}': {e}") from e

        param_optim_1 = None
        if self.linear_solver_param_optim_1 is not None:
            try:
                param_optim_1 = json.loads(self.linear_solver_param_optim_1)
            except Exception as e:
                raise ValueError(f"Failed to parse linear_solver_param_optim_1: {e}") from e

        param_optim_2 = None
        if self.linear_solver_param_optim_2 is not None:
            try:
                param_optim_2 = json.loads(self.linear_solver_param_optim_2)
            except Exception as e:
                raise ValueError(f"Failed to parse linear_solver_param_optim_2: {e}") from e

        param = None
        if self.linear_solver_param is not None:
            try:
                param = json.loads(self.linear_solver_param)
            except Exception as e:
                raise ValueError(f"Failed to parse linear_solver_param: {e}") from e

        return SolverPresets(
            id=self.id,
            name=self.name,
            linear_solver=self.linear_solver,
            min_antares_version=min_version,
            max_antares_version=max_version,
            linear_solver_param_optim_1=param_optim_1,
            linear_solver_param_optim_2=param_optim_2,
            linear_solver_param=param,
            use_optim_1_basis_next_week=self.use_optim_1_basis_next_week,
            use_optim_1_basis_optim_2=self.use_optim_1_basis_optim_2,
        )

    @classmethod
    def from_model(cls, dto: SolverPresets) -> "SolverPresetsDB":
        data = dto.model_dump(exclude_none=True, exclude={"other_options"})
        if dto.min_antares_version is not None:
            data["min_antares_version"] = str(dto.min_antares_version)
        if dto.max_antares_version is not None:
            data["max_antares_version"] = str(dto.max_antares_version)
        for key in [
            "linear_solver_param_optim_1",
            "linear_solver_param_optim_2",
            "linear_solver_param",
        ]:
            if key in data and data[key] is not None:
                data[key] = json.dumps(data[key])
        return cls(**data)

    @override
    def __str__(self) -> str:
        return f"Solver presets #{self.id} '{self.name}' (solver: {self.linear_solver})"

    @override
    def __repr__(self) -> str:
        return (
            f"<SolverPresetsModel(id={self.id!r},"
            f" name={self.name!r},"
            f" linear_solver={self.linear_solver!r},"
            f" min_antares_version={self.min_antares_version!r},"
            f" max_antares_version={self.max_antares_version!r},"
            f" linear_solver_param_optim_1={self.linear_solver_param_optim_1!r},"
            f" linear_solver_param_optim_2={self.linear_solver_param_optim_2!r},"
            f" linear_solver_param={self.linear_solver_param!r},"
            f" use_optim_1_basis_next_week={self.use_optim_1_basis_next_week!r},"
            f" use_optim_1_basis_optim_2={self.use_optim_1_basis_optim_2!r})>"
        )


def apply_update_solver_presets(
    solver_presets_db: SolverPresetsDB,
    solver_presets_update: SolverPresetsUpdate,
) -> SolverPresetsDB:
    # Merge existing DTO with update DTO
    current_dto_dict = solver_presets_db.to_model().model_dump()
    update_dict = solver_presets_update.model_dump(exclude_none=True)
    merged_dict = {**current_dto_dict, **update_dict}

    # Validate the merged data
    updated_dto = SolverPresets.model_validate(merged_dict)

    # turn back to model
    return SolverPresetsDB.from_model(updated_dto)


def is_version_covered_by_config(
    solver_presets: SolverPresets,
    solver_version: SolverVersion,
) -> bool:
    """
    Check if the given solver presets are compatible with the specified Antares study version.

    :param solver_presets: The solver presets to check.
    :param study_version: The Antares study version to check against.
    :return: True if the presets are compatible, False otherwise.
    """
    if solver_presets.min_antares_version:
        if solver_version < solver_presets.min_antares_version:
            return False

    if solver_presets.max_antares_version:
        if solver_version > solver_presets.max_antares_version:
            return False

    return True
