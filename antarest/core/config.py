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
from typing import Annotated, Any, ClassVar, Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from antarest.core.roles import RoleType


class ConfigBaseModel(BaseModel):
    """Base model for all configuration classes."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra="ignore",
        validate_default=True,
    )

DEFAULT_WORKSPACE_NAME = "default"


class LauncherType(StrEnum):
    SLURM = "slurm"
    LOCAL = "local"


class InternalMatrixFormat(StrEnum):
    TSV = "tsv"
    HDF = "hdf"
    PARQUET = "parquet"
    FEATHER = "feather"


class ExternalAuthConfig(ConfigBaseModel):
    """Sub config object dedicated to external auth service."""

    url: str | None = None
    default_group_role: RoleType = RoleType.READER
    add_ext_groups: bool = False
    group_mapping: dict[str, str] = Field(default_factory=dict)


class SecurityConfig(ConfigBaseModel):
    """Sub config object dedicated to security."""

    jwt_key: str = ""
    admin_pwd: str = ""
    disabled: bool = False
    external_auth: ExternalAuthConfig = Field(default_factory=ExternalAuthConfig)

    @model_validator(mode="before")
    @classmethod
    def flatten_nested_paths(cls, data: Any) -> Any:
        """Flatten nested YAML paths: jwt.key -> jwt_key, login.admin.pwd -> admin_pwd."""
        if not isinstance(data, dict):
            return data

        data = dict(data)  # Make a copy

        # Handle jwt.key -> jwt_key
        if "jwt" in data and isinstance(data["jwt"], dict):
            jwt_data = data.pop("jwt")
            if "key" in jwt_data and "jwt_key" not in data:
                data["jwt_key"] = jwt_data["key"]

        # Handle login.admin.pwd -> admin_pwd
        if "login" in data and isinstance(data["login"], dict):
            login_data = data.pop("login")
            if "admin" in login_data and isinstance(login_data["admin"], dict):
                admin_data = login_data["admin"]
                if "pwd" in admin_data and "admin_pwd" not in data:
                    data["admin_pwd"] = admin_data["pwd"]

        return data


class WorkspaceConfig(ConfigBaseModel):
    """Sub config object dedicated to workspace."""

    filter_in: list[str] = Field(default_factory=lambda: [".*"])
    filter_out: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    path: Path = Path()


class DbConfig(ConfigBaseModel):
    """Sub config object dedicated to db."""

    db_url: str = Field(default="", alias="url")
    db_admin_url: str | None = Field(default=None, alias="admin_url")
    db_connect_timeout: int = 10
    pool_recycle: int | None = None
    pool_pre_ping: bool = False
    pool_use_null: bool = False
    pool_max_overflow: int = 10
    pool_size: int = 5
    pool_use_lifo: bool = False


class StorageConfig(ConfigBaseModel):
    """Sub config object dedicated to study module."""

    matrixstore: Path = Path("./matrixstore")
    archive_dir: Path = Path("./archives")
    tmp_dir: Path = Field(default_factory=lambda: Path(tempfile.gettempdir()))
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
    snapshot_retention_days: int = 7
    matrixstore_format: InternalMatrixFormat = InternalMatrixFormat.TSV
    blobstore: Path = Path("./blobstore")
    blob_gc_sleeping_time: int = 86400
    blob_gc_dry_run: bool = False
    variable_view_gc_sleeping_time: int = 3600
    variable_view_gc_dry_run: bool = False
    variable_view_gc_retention_days: int = 30
    watcher_scan_sleeping_time: int = 60
    watcher_scan_dry_run: bool = False

    @field_validator("workspaces", mode="before")
    @classmethod
    def convert_workspaces(cls, v: Any) -> dict[str, WorkspaceConfig]:
        """Convert dict entries to WorkspaceConfig objects."""
        if isinstance(v, dict):
            return {
                key: WorkspaceConfig.model_validate(val) if isinstance(val, dict) else val for key, val in v.items()
            }
        return v

    @staticmethod
    def validate_workspaces(workspaces: dict[str, WorkspaceConfig], desktop_mode: bool) -> None:
        """Validate that no two workspaces have overlapping paths."""
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

    @staticmethod
    def system_workspaces() -> dict[str, WorkspaceConfig]:
        """Generate system workspaces for desktop mode."""
        if platform.system().lower() == "linux":
            return {"local": WorkspaceConfig(path=Path("/"))}
        elif platform.system().lower() == "windows":
            # TODO: After update to python 3.12 use os.listdrives()
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.isdir(f"{d}:\\")]
            return {drive: WorkspaceConfig(path=Path(drive)) for drive in drives}
        else:
            raise NotImplementedError("System workspaces are only implemented for Linux and Windows")


class NbCoresConfig(ConfigBaseModel):
    """Configuration for the number of CPU cores."""

    min: int = 1
    default: int = 22
    max: int = 24

    def to_json(self) -> dict[str, int]:
        """
        Return parameters for ReactJS Material UI.

        Returns:
            A dictionary: `{"min": min, "defaultValue": default, "max": max}`.
        """
        return {"min": self.min, "defaultValue": self.default, "max": self.max}

    @model_validator(mode="after")
    def validate_range(self) -> "NbCoresConfig":
        """Validate that 1 <= min <= default <= max."""
        if not (1 <= self.min <= self.default <= self.max):
            raise ValueError(f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}")
        return self


class TimeLimitConfig(ConfigBaseModel):
    """
    Configuration for the time limit for a job.

    Attributes:
        min: minimum allowed value for the time limit (in hours).
        default: default value for the time limit (in hours).
        max: maximum allowed value for the time limit (in hours).
    """

    min: int = 1
    default: int = 48
    max: int = 48

    def to_json(self) -> dict[str, int]:
        """
        Return parameters for ReactJS Material UI.

        Returns:
            A dictionary: `{"min": min, "defaultValue": default, "max": max}`.
        """
        return {"min": self.min, "defaultValue": self.default, "max": self.max}

    @model_validator(mode="after")
    def validate_range(self) -> "TimeLimitConfig":
        """Validate that 1 <= min <= default <= max."""
        if not (1 <= self.min <= self.default <= self.max):
            raise ValueError(f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}")
        return self


class LocalConfig(ConfigBaseModel):
    """Sub config object dedicated to launcher module (local)."""

    type: Literal["local"] = "local"
    id: str
    name: str
    binaries: dict[str, Path] = Field(default_factory=dict)
    enable_nb_cores_detection: bool = True
    nb_cores: NbCoresConfig = Field(default_factory=NbCoresConfig)
    time_limit: TimeLimitConfig = Field(default_factory=TimeLimitConfig)
    xpress_dir: str | None = None
    local_workspace: Path = Path("./local_workspace")

    @field_validator("binaries", mode="before")
    @classmethod
    def convert_binaries(cls, v: Any) -> dict[str, Path]:
        """Convert binaries dict values to Path objects."""
        if isinstance(v, dict):
            return {str(k): Path(val) for k, val in v.items()}
        return v

    @model_validator(mode="after")
    def apply_cpu_detection(self) -> "LocalConfig":
        """Apply automatic CPU core detection if enabled."""
        if self.enable_nb_cores_detection:
            detected = self._autodetect_nb_cores()
            return self.model_copy(update={"nb_cores": NbCoresConfig.model_validate(detected)})
        return self

    @staticmethod
    def _autodetect_nb_cores() -> dict[str, int]:
        """Automatically detect the number of cores available on the machine."""
        min_cpu = 1
        max_cpu = multiprocessing.cpu_count()
        default = max(min_cpu, max_cpu - 2)
        return {"min": min_cpu, "max": max_cpu, "default": default}


class SlurmConfig(ConfigBaseModel):
    """Sub config object dedicated to launcher module (slurm)."""

    type: Literal["slurm"] = "slurm"
    id: str
    name: str
    local_workspace: Path = Path()
    username: str = ""
    hostname: str = ""
    port: int = 0
    private_key_file: Path = Path()
    key_password: str = ""
    password: str = ""
    default_wait_time: int = 0
    time_limit: TimeLimitConfig = Field(default_factory=TimeLimitConfig)
    nb_cores: NbCoresConfig = Field(default_factory=NbCoresConfig)
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    partition: str = ""
    max_cores: int = 64
    antares_versions_on_remote_server: list[str] = Field(default_factory=list)
    enable_nb_cores_detection: bool = False

    @model_validator(mode="before")
    @classmethod
    def handle_backward_compat(cls, data: Any) -> Any:
        """Handle backward compatibility for old config formats."""
        if not isinstance(data, dict):
            return data

        data = dict(data)  # Make a copy

        # Handle old default_n_cpu field -> nb_cores
        if "default_n_cpu" in data:
            nb_cores = dict(data.get("nb_cores", {})) if data.get("nb_cores") else {"min": 1, "default": 22, "max": 24}
            default_n_cpu = int(data.pop("default_n_cpu"))
            nb_cores["default"] = default_n_cpu
            nb_cores["min"] = min(nb_cores.get("min", 1), default_n_cpu)
            nb_cores["max"] = max(nb_cores.get("max", 24), default_n_cpu)
            data["nb_cores"] = nb_cores

        # Convert default_time_limit from seconds to hours for time_limit
        if "default_time_limit" in data:
            seconds = data.pop("default_time_limit")
            hours = seconds // 3600
            data["time_limit"] = {"min": 1, "default": hours, "max": hours}

        return data

    @model_validator(mode="after")
    def check_cpu_detection(self) -> "SlurmConfig":
        """Raise error if CPU auto-detection is enabled (not supported for SLURM)."""
        if self.enable_nb_cores_detection:
            raise NotImplementedError("NB Cores auto-detection is not implemented for SLURM server")
        return self


class InvalidConfigurationError(Exception):
    """
    Exception raised when an attempt is made to retrieve a property
    of a launcher that doesn't exist in the configuration.
    """

    def __init__(self, launcher: str):
        msg = f"Configuration is not available for the '{launcher}' launcher"
        super().__init__(msg)


# Discriminated union type for launcher configurations
LauncherConfigType = Annotated[Union[LocalConfig, SlurmConfig], Field(discriminator="type")]


class LauncherConfig(ConfigBaseModel):
    """Sub config object dedicated to launcher module."""

    default: str = "local"
    configs: list[LauncherConfigType] | None = Field(default=None, alias="launchers")
    batch_size: int = 9999

    @model_validator(mode="after")
    def validate_default_exists(self) -> "LauncherConfig":
        """Validate that the default launcher ID exists in the configs list."""
        if self.configs and not any(launcher.id == self.default for launcher in self.configs):
            raise InvalidConfigurationError(f"Default launcher id '{self.default}' not found in launcher configs")
        return self

    def get_slurm_configs(self) -> list[SlurmConfig]:
        """Return all SLURM launcher configurations."""
        return [cfg for cfg in self.configs or [] if isinstance(cfg, SlurmConfig)]


class LoggingConfig(ConfigBaseModel):
    """Sub config object dedicated to logging."""

    logfile: Path | None = None
    json_format: bool = Field(default=False, alias="json")
    level: str = "INFO"


class RedisConfig(ConfigBaseModel):
    """Sub config object dedicated to redis."""

    host: str = "localhost"
    port: int = 6379
    password: str | None = None


class EventBusConfig(ConfigBaseModel):
    """Sub config object dedicated to eventbus module."""

    pass


class CacheConfig(ConfigBaseModel):
    """Sub config object dedicated to cache module."""

    checker_delay: float = 0.2  # in seconds


class RemoteWorkerConfig(ConfigBaseModel):
    """Configuration for a remote worker."""

    name: str
    queues: list[str] = Field(default_factory=list)


class TaskConfig(ConfigBaseModel):
    """Sub config object dedicated to the task module."""

    max_workers: int = 5
    remote_workers: list[RemoteWorkerConfig] = Field(default_factory=list)


class ServerConfig(ConfigBaseModel):
    """Sub config object dedicated to the server."""

    worker_threadpool_size: int = 5
    services: list[str] = Field(default_factory=list)


class PrometheusConfig(ConfigBaseModel):
    """
    Sub config object dedicated to prometheus metrics.

    Attributes:
        multiprocess: if True, metrics of workers will be aggregated before exposition.
                      Environment variable `PROMETHEUS_MULTIPROC_DIR` must be set.
    """

    multiprocess: bool = False


class MetricsConfig(ConfigBaseModel):
    """
    Sub config object dedicated to metrics.

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
    def build_redis_url(redis_config: RedisConfig, db: int) -> str:
        """Build a Redis URL from RedisConfig."""
        password_part = f":{redis_config.password}@" if redis_config.password else ""
        return f"redis://{password_part}{redis_config.host}:{redis_config.port}/{db}"


class Config(ConfigBaseModel):
    """Root server config."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    launcher: LauncherConfig = Field(default_factory=LauncherConfig)
    db: DbConfig = Field(default_factory=DbConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    debug: bool = True
    resources_path: Path = Path()
    redis: RedisConfig | None = None
    eventbus: EventBusConfig = Field(default_factory=EventBusConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    tasks: TaskConfig = Field(default_factory=TaskConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    root_path: str = ""
    api_prefix: str = ""
    desktop_mode: bool = False

    @model_validator(mode="after")
    def post_process(self) -> "Config":
        """Post-process config: validate storage, add system workspaces, and configure celery."""
        result = self

        # 1. Validate and enhance storage for desktop_mode
        StorageConfig.validate_workspaces(result.storage.workspaces, result.desktop_mode)
        if result.desktop_mode:
            new_workspaces = {**result.storage.workspaces, **StorageConfig.system_workspaces()}
            new_storage = result.storage.model_copy(update={"workspaces": new_workspaces})
            result = result.model_copy(update={"storage": new_storage})

        # 2. Build celery URLs from redis config if not explicitly set
        if result.redis and not result.celery.broker_url:
            redis_url = CeleryConfig.build_redis_url(result.redis, CeleryConfig.REDIS_DB)
            new_celery = result.celery.model_copy(update={"broker_url": redis_url, "result_backend": redis_url})
            result = result.model_copy(update={"celery": new_celery})

        return result

    @classmethod
    def from_yaml_file(cls, file: Path, res: Path | None = None) -> "Config":
        """
        Parse config from yaml file.

        Args:
            file: yaml path
            res: resources path is not present in yaml file.

        Returns:
            Parsed Config object.
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
