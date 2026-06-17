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

import multiprocessing
import os
import platform
import string
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

import yaml
from antares.study.version import SolverVersion
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from antarest.core.roles import RoleType
from antarest.core.utils.archives import ArchiveFormat
from antarest.output.storage.output_storage import OutputStorageType
from antarest.study.model import DEFAULT_WORKSPACE_NAME


class LauncherType(StrEnum):
    SLURM = "slurm"
    LOCAL = "local"


class InternalMatrixFormat(StrEnum):
    TSV = "tsv"
    HDF = "hdf"
    PARQUET = "parquet"
    FEATHER = "feather"


class ConfigBaseModel(BaseModel):
    """Base model for all configuration classes."""

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore", validate_default=True)


class ExternalAuthConfig(ConfigBaseModel):
    """
    Sub config object dedicated to external auth service
    """

    url: str | None = None
    default_group_role: RoleType = RoleType.READER
    add_ext_groups: bool = False
    group_mapping: dict[str, str] = Field(default_factory=dict)


class SecurityConfig(ConfigBaseModel):
    """
    Sub config object dedicated to security
    """

    jwt_key: str = ""
    admin_pwd: str = ""
    disabled: bool = False
    external_auth: ExternalAuthConfig = Field(default_factory=ExternalAuthConfig)

    @model_validator(mode="before")
    @classmethod
    def _flatten_nested_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "jwt" in data:
            data.setdefault("jwt_key", data.pop("jwt", {}).get("key", ""))
        if "login" in data:
            data.setdefault("admin_pwd", data.pop("login", {}).get("admin", {}).get("pwd", ""))
        return data


class WorkspaceConfig(ConfigBaseModel):
    """
    Sub config object dedicated to workspace
    """

    filter_in: list[str] = Field(default_factory=lambda: [".*"])
    filter_out: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    path: Path = Field(default_factory=Path)


class DbConfig(ConfigBaseModel):
    """
    Sub config object dedicated to db
    """

    # populate_by_name so DbConfig can be creating using DbConfig(url=...) or DbConfig(db_url=...)
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    db_url: str = Field(default="", alias="url")
    db_admin_url: str | None = Field(default=None, alias="admin_url")
    db_connect_timeout: int = 10
    pool_recycle: int | None = None
    pool_pre_ping: bool = False
    pool_use_null: bool = False
    pool_max_overflow: int = 10
    pool_size: int = 5
    pool_use_lifo: bool = False


class V2OutputStorageConfig(ConfigBaseModel):
    """
    Configuration for "new style" internal output storage
    """

    enable: bool = False
    archive_dir: Path = Path("./output-archives")
    variables_dir: Path = Path("./output-variables")


class OutOfStudyFileOutputStorageConfig(ConfigBaseModel):
    """
    Configuration for output storage in a single dir for all studies
    """

    storage_dir: Path = Path("./outputs")

    @model_validator(mode="after")
    def _create_storage_dir(self) -> "OutOfStudyFileOutputStorageConfig":
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        return self


class OutputStorageConfig(ConfigBaseModel):
    """Configuration for output storage"""

    v2: V2OutputStorageConfig = V2OutputStorageConfig()
    out_of_study: OutOfStudyFileOutputStorageConfig = Field(default_factory=OutOfStudyFileOutputStorageConfig)
    default_storage_type: OutputStorageType = OutputStorageType.IN_STUDY_FILE_TREE

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, data: Any) -> Any:
        if "out_of_study" in data:
            data["out_of_study"] = OutOfStudyFileOutputStorageConfig.model_validate(data["out_of_study"])
        if "default_storage_type" in data:
            default_storage_type = OutputStorageType(data["default_storage_type"])
            data["default_storage_type"] = default_storage_type
        return data

    @model_validator(mode="after")
    def _validate_default_storage_type(self) -> "OutputStorageConfig":
        if self.default_storage_type == OutputStorageType.V2 and not self.v2.enable:
            raise ValueError("You cannot set v2 storage as your default storage and not enable it")
        return self


class StudyStorageConfig(ConfigBaseModel):
    """
    Sub config object dedicated to study storage configuration (from study.storage in YAML)
    """

    database_mode_enabled: bool = False


class StorageConfig(ConfigBaseModel):
    """
    Sub config object dedicated to study module
    """

    matrixstore: Path = Path("./matrixstore")
    archive_dir: Path = Path("./archives")
    archive_format: ArchiveFormat = ArchiveFormat.ZIP
    tmp_dir: Path = Path(tempfile.gettempdir())
    workspaces: dict[str, WorkspaceConfig] = Field(default_factory=dict)
    allow_deletion: bool = False
    watcher_lock: bool = True
    watcher_lock_delay: int = 10
    download_default_expiration_timeout_minutes: int = 1440
    matrix_gc_sleeping_time: int = 3600
    matrix_gc_dry_run: bool = False
    matrix_gc_retention_time: int = 3600
    auto_archive_threshold_days: int = 60
    auto_archive_dry_run: bool = False
    auto_archive_sleeping_time: int = 3600
    auto_archive_cron: str = "0 20-23,0-7 * * * "
    snapshot_retention_days: int = 7
    matrixstore_format: InternalMatrixFormat = InternalMatrixFormat.TSV
    blobstore: Path = Path("./blobstore")
    blob_gc_sleeping_time: int = 86400
    blob_gc_dry_run: bool = False
    variable_view_gc_sleeping_time: int = 3600
    variable_view_gc_dry_run: bool = False
    variable_view_gc_retention_days: int = 30
    watcher_scan_sleeping_time: int = 900
    watcher_scan_dry_run: bool = False
    tasks_gc_retention_days: int = 30
    tasks_gc_sleeping_time: int = 86400
    tasks_gc_dry_run: bool = False
    disk_usage_log_sleeping_time: int = 300
    disk_usage_log_cron: str = "0 * * * *"
    disk_space_analyzer_sleeping_time: int = 300
    disk_space_analyzer_cron: str = "0 1 * * *"
    study_storage: StudyStorageConfig = Field(default_factory=StudyStorageConfig)
    output: OutputStorageConfig = Field(default_factory=OutputStorageConfig)

    @field_validator("workspaces", mode="before")
    @classmethod
    def convert_workspaces(cls, v: Any) -> Any:
        """Convert dict entries to WorkspaceConfig objects."""
        if isinstance(v, dict):
            return {
                key: WorkspaceConfig.model_validate(val) if isinstance(val, dict) else val for key, val in v.items()
            }
        return v

    @model_validator(mode="before")
    @classmethod
    def _preprocess(cls, data: Any) -> Any:
        """Flatten nested YAML keys and validate mutual exclusions."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # Flatten study.storage → study_storage
        if "study" in data and isinstance(data["study"], dict):
            data.setdefault("study_storage", data.pop("study").get("storage", {}))
        # Mutual exclusion check
        if data.get("auto_archive_sleeping_time") and data.get("auto_archive_cron"):
            raise ValueError("auto_archive_sleeping_time and auto_archive_cron cannot be used together")
        return data

    @classmethod
    def validate_workspaces(cls, workspaces: dict[str, WorkspaceConfig], desktop_mode: bool) -> None:
        """
        Validate that no two workspaces have overlapping paths.
        """
        workspace_names = list(workspaces.keys())
        only_default = workspace_names == [DEFAULT_WORKSPACE_NAME]
        if desktop_mode and not only_default:
            raise ValueError(
                f"Desktop mode is on, only default workspace should be configured. Instead conf has {workspace_names}"
            )

        workspace_name_by_path = [(config.path, name) for name, config in workspaces.items()]
        for path, name in workspace_name_by_path:
            for path2, name2 in workspace_name_by_path:
                if name != name2 and path.is_relative_to(path2):
                    raise ValueError(
                        f"Overlapping workspace paths found: '{name}' and '{name2}' '{path}' is relative to '{path2}' "
                    )

    @classmethod
    def system_workspaces(cls) -> dict[str, WorkspaceConfig]:
        if platform.system().lower() == "linux":
            return {"local": WorkspaceConfig(path=Path("/"))}
        elif platform.system().lower() == "windows":
            # TODO : After update to python 3.12 use os.listdrives()
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.isdir(f"{d}:\\")]
            return {drive: WorkspaceConfig(path=Path(drive)) for drive in drives}
        else:
            raise NotImplementedError("System workspaces are only implemented for Linux and Windows")


class NbCoresConfig(ConfigBaseModel):
    """
    The NBCoresConfig class is designed to manage the configuration of the number of CPU cores
    """

    min: int = 1
    default: int = 22
    max: int = 24

    def to_json(self) -> dict[str, int]:
        """
        Retrieves the number of cores parameters, returning a dictionary containing the values "min"
        (minimum allowed value), "defaultValue" (default value), and "max" (maximum allowed value)

        Returns:
            A dictionary: `{"min": min, "defaultValue": default, "max": max}`.
            Because ReactJs Material UI expects "min", "defaultValue" and "max" keys.
        """
        return {"min": self.min, "defaultValue": self.default, "max": self.max}

    @model_validator(mode="after")
    def _validate_range(self) -> "NbCoresConfig":
        """validation of CPU configuration"""
        if 1 <= self.min <= self.default <= self.max:
            return self
        msg = f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}"
        raise ValueError(msg)


class TimeLimitConfig(ConfigBaseModel):
    """
    The TimeLimitConfig class is designed to manage the configuration of the time limit for a job.

    Attributes:
        min: int: minimum allowed value for the time limit (in hours).
        default: int: default value for the time limit (in hours).
        max: int: maximum allowed value for the time limit (in hours).
    """

    min: int = 1
    default: int = 48
    max: int = 48

    def to_json(self) -> dict[str, int]:
        """
        Retrieves the time limit parameters, returning a dictionary containing the values "min"
        (minimum allowed value), "defaultValue" (default value), and "max" (maximum allowed value)

        Returns:
            A dictionary: `{"min": min, "defaultValue": default, "max": max}`.
            Because ReactJs Material UI expects "min", "defaultValue" and "max" keys.
        """
        return {"min": self.min, "defaultValue": self.default, "max": self.max}

    @model_validator(mode="after")
    def _validate_range(self) -> "TimeLimitConfig":
        """validation of time limit configuration"""
        if 1 <= self.min <= self.default <= self.max:
            return self
        msg = f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}"
        raise ValueError(msg)


class LocalConfig(ConfigBaseModel):
    """Sub config object dedicated to launcher module (local)"""

    id: str
    name: str
    type: ClassVar[LauncherType] = LauncherType.LOCAL
    binaries: dict[SolverVersion, Path] = Field(default_factory=dict)
    enable_nb_cores_detection: bool = True
    nb_cores: NbCoresConfig = Field(default_factory=NbCoresConfig)
    time_limit: TimeLimitConfig = Field(default_factory=TimeLimitConfig)
    xpress_dir: str | None = None
    local_workspace: Path = Path("./local_workspace")

    @field_validator("binaries", mode="before")
    @classmethod
    def _parse_binaries(cls, v: Any) -> Any:
        """Coerce string keys/values to SolverVersion/Path."""
        if isinstance(v, dict):
            return {
                SolverVersion.parse(str(k)) if not isinstance(k, SolverVersion) else k: Path(val)
                for k, val in v.items()
            }
        return v

    @model_validator(mode="before")
    @classmethod
    def apply_cpu_detection(cls, data: Any) -> Any:
        """Inject detected CPU core counts into data before construction."""
        if isinstance(data, dict) and data.get("enable_nb_cores_detection", True):
            data = {**data, "nb_cores": cls._autodetect_nb_cores()}
        return data

    @classmethod
    def _autodetect_nb_cores(cls) -> dict[str, int]:
        """
        Automatically detects the number of cores available on the user's machine
        Returns: Instance of NbCoresConfig
        """
        min_cpu = NbCoresConfig().min
        max_cpu = multiprocessing.cpu_count()
        default = max(min_cpu, max_cpu - 2)
        return {"min": min_cpu, "max": max_cpu, "default": default}


class SlurmConfig(ConfigBaseModel):
    """
    Sub config object dedicated to launcher module (slurm)
    """

    id: str
    name: str
    type: ClassVar[LauncherType] = LauncherType.SLURM
    local_workspace: Path = Field(default_factory=Path)
    username: str = ""
    hostname: str = ""
    port: int = 0
    private_key_file: Path = Field(default_factory=Path)
    key_password: str = ""
    password: str = ""
    default_wait_time: int = 0
    time_limit: TimeLimitConfig = Field(default_factory=TimeLimitConfig)
    nb_cores: NbCoresConfig = Field(default_factory=NbCoresConfig)
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    partition: str = ""
    max_cores: int = 64
    antares_versions_on_remote_server: list[SolverVersion] = Field(default_factory=list)
    enable_nb_cores_detection: bool = False

    @field_validator("antares_versions_on_remote_server", mode="before")
    @classmethod
    def _parse_versions(cls, v: Any) -> Any:
        """Coerce string items to SolverVersion."""
        if isinstance(v, list):
            return [SolverVersion.parse(str(item)) if not isinstance(item, SolverVersion) else item for item in v]
        return v

    @model_validator(mode="before")
    @classmethod
    def handle_backward_compatibility(cls, data: Any) -> Any:
        """Handle backward compatibility for old config formats."""
        if not isinstance(data, dict):
            return data

        data = dict(data)  # Make a copy
        # Handle old default_n_cpu field -> nb_cores
        if "default_n_cpu" in data:
            nb_cores = data.get("nb_cores", NbCoresConfig().model_dump())
            default_n_cpu = int(data.pop("default_n_cpu"))
            nb_cores["default"] = default_n_cpu
            nb_cores["min"] = min(nb_cores["min"], default_n_cpu)
            nb_cores["max"] = max(nb_cores["max"], default_n_cpu)
            data["nb_cores"] = nb_cores

        max_time = data.pop("default_time_limit", TimeLimitConfig().max * 3600) / 3600
        data["time_limit"] = TimeLimitConfig(min=1, default=max_time, max=max_time)
        return data


class InvalidConfigurationError(Exception):
    """
    Exception raised when an attempt is made to retrieve a property
    of a launcher that doesn't exist in the configuration.
    """

    def __init__(self, launcher: str):
        msg = f"Configuration is not available for the '{launcher}' launcher"
        super().__init__(msg)


class LauncherConfig(ConfigBaseModel):
    """
    Sub config object dedicated to launcher module
    """

    default: str = Field(default="local")
    configs: list[LocalConfig | SlurmConfig] | None = None
    batch_size: int = 9999

    @model_validator(mode="before")
    @classmethod
    def _remap_launchers(cls, data: Any) -> Any:
        """Remap the 'launchers' YAML key to 'configs', dispatching each entry by type."""
        if not isinstance(data, dict) or "launchers" not in data:
            return data
        data = dict(data)
        raw_launchers = data.pop("launchers")
        configs: list[Any] = []
        for launcher in raw_launchers:
            launcher_type = launcher.get("type")
            if launcher_type == LauncherType.LOCAL:
                configs.append(LocalConfig.model_validate(launcher))
            elif launcher_type == LauncherType.SLURM:
                configs.append(SlurmConfig.model_validate(launcher))
            else:
                raise ValueError(f"Unknown launcher type: {launcher_type!r}")
        data["configs"] = configs
        return data

    @model_validator(mode="after")
    def _validate_default_launcher(self) -> "LauncherConfig":
        if self.configs:
            if not any(launcher.id == self.default for launcher in self.configs):
                ids = [launcher.id for launcher in self.configs]
                raise ValueError(f"Default launcher id '{self.default}' not found in launcher configs, got {ids}")
        return self

    def get_slurm_configs(self) -> list[SlurmConfig]:
        return [cfg for cfg in self.configs or [] if isinstance(cfg, SlurmConfig)]


class LoggingConfig(ConfigBaseModel):
    """
    Sub config object dedicated to logging
    """

    logfile: Path | None = None
    json_format: bool = Field(default=False, alias="json")
    level: str = "INFO"


class RedisConfig(ConfigBaseModel):
    """
    Sub config object dedicated to redis
    """

    host: str = "localhost"
    port: int = 6379
    password: str | None = None


class EventBusConfig(ConfigBaseModel):
    """
    Sub config object dedicated to eventbus module
    """


class CacheConfig(ConfigBaseModel):
    """
    Sub config object dedicated to cache module
    """

    checker_delay: float = 0.2  # in seconds


class RemoteWorkerConfig(ConfigBaseModel):
    name: str
    queues: list[str] = Field(default_factory=list)


class TaskConfig(ConfigBaseModel):
    """
    Sub config object dedicated to the task module
    """

    max_workers: int = 5
    remote_workers: list[RemoteWorkerConfig] = Field(default_factory=list)


class ServerConfig(ConfigBaseModel):
    """
    Sub config object dedicated to the server
    """

    worker_threadpool_size: int = 5
    services: list[str] = Field(default_factory=list)


class PrometheusConfig(ConfigBaseModel):
    """
    Sub config object dedicated to prometheus metrics

    Attributes:
        multiprocess: if True, metrics of workers will be aggregated before exposition.
                      Environment variable `PROMETHEUS_MULTIPROC_DIR` must be set.
    """

    multiprocess: bool = False


class MetricsConfig(ConfigBaseModel):
    """
    Sub config object dedicated to metrics

    Attributes:
        prometheus: if not None, metrics will be exposed in prometheus format
    """

    prometheus: PrometheusConfig | None = None


class CeleryConfig(ConfigBaseModel):
    """
    Sub config object dedicated to Celery technical configuration.

    Attributes:
        broker_url: URL of the message broker (built from RedisConfig)
        result_backend: URL of the result backend (built from RedisConfig)
        result_expires: Time in seconds before task results expire
    """

    # Redis database number for Celery (broker + results)
    REDIS_DB: ClassVar[int] = 1

    broker_url: str = ""
    result_backend: str = ""
    result_expires: int = 86400  # 24 hours

    @staticmethod
    def _build_redis_url(redis_config: RedisConfig, db: int) -> str:
        password_part = f":{redis_config.password}@" if redis_config.password else ""
        return f"redis://{password_part}{redis_config.host}:{redis_config.port}/{db}"

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, data: Any) -> Any:
        redis_url = ""
        if "redis_config" in data:
            redis_url = cls._build_redis_url(data["redis_config"], cls.REDIS_DB)

        data["broker_url"] = data.get("broker_url", redis_url)
        data["result_backend"] = data.get("result_backend", redis_url)

        return data


class Config(ConfigBaseModel):
    """
    Root server config
    """

    server: ServerConfig = Field(default_factory=ServerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    launcher: LauncherConfig = Field(default_factory=LauncherConfig)
    db: DbConfig = Field(default_factory=DbConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    debug: bool = True
    resources_path: Path = Field(default_factory=Path)
    redis: RedisConfig | None = None
    eventbus: EventBusConfig = Field(default_factory=EventBusConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    tasks: TaskConfig = Field(default_factory=TaskConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    root_path: str = ""
    api_prefix: str = ""
    desktop_mode: bool = False

    @model_validator(mode="before")
    @classmethod
    def _model_validator(cls, data: Any) -> Any:
        desktop_mode = data.get("desktop_mode", False)
        storage_config = cls._build_storage_config(data, desktop_mode)
        redis_config = RedisConfig.model_validate(data["redis"]) if "redis" in data else None
        data["storage"] = storage_config
        data["redis"] = redis_config

        return data

    @classmethod
    def _build_storage_config(cls, data: Any, desktop_mode: bool) -> StorageConfig:
        if "storage" in data:
            storage_data = data["storage"]
            storage_config = StorageConfig.model_validate(storage_data)
            # Desktop-mode workspace validation and system workspace injection only when
            # parsing from a raw dict (i.e. YAML config). When constructing Config directly
            # with pre-built objects, skip these semantic checks.
            if isinstance(storage_data, dict):
                workspaces = dict(storage_config.workspaces)
                StorageConfig.validate_workspaces(workspaces, desktop_mode)
                if desktop_mode:
                    workspaces = {**workspaces, **StorageConfig.system_workspaces()}
                    storage_config = storage_config.model_copy(update={"workspaces": workspaces})
        else:
            storage_config = StorageConfig()
        return storage_config

    @classmethod
    def from_yaml_file(cls, file: Path, res: Path | None = None) -> "Config":
        """
        Parse config from yaml file.

        Args:
            file: yaml path
            res: resources path is not present in yaml file.

        Returns:

        """
        with open(file) as f:
            data = yaml.safe_load(f)
        if res is not None:
            data["resources_path"] = res
        return cls.model_validate(data)

    def get_workspace_path(self, *, workspace: str = DEFAULT_WORKSPACE_NAME) -> Path:
        """
        Get workspace path from config file.

        Args:
            workspace: Workspace name.

        Returns:
            Absolute (or relative) path to the workspace directory.
        """
        try:
            return self.storage.workspaces[workspace].path
        except KeyError:
            raise ValueError(f"Workspace '{workspace}' not found in config") from None
