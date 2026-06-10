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
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

import yaml
from antares.study.version import SolverVersion

from antarest.core.model import JSON
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


@dataclass(frozen=True)
class ExternalAuthConfig:
    """
    Sub config object dedicated to external auth service
    """

    url: str | None = None
    default_group_role: RoleType = RoleType.READER
    add_ext_groups: bool = False
    group_mapping: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JSON) -> "ExternalAuthConfig":
        defaults = cls()
        return cls(
            url=data.get("url", defaults.url),
            default_group_role=(
                RoleType(data["default_group_role"]) if "default_group_role" in data else defaults.default_group_role
            ),
            add_ext_groups=data.get("add_ext_groups", defaults.add_ext_groups),
            group_mapping=data.get("group_mapping", defaults.group_mapping),
        )


@dataclass(frozen=True)
class SecurityConfig:
    """
    Sub config object dedicated to security
    """

    jwt_key: str = ""
    admin_pwd: str = ""
    disabled: bool = False
    external_auth: ExternalAuthConfig = ExternalAuthConfig()

    @classmethod
    def from_dict(cls, data: JSON) -> "SecurityConfig":
        defaults = cls()
        return cls(
            jwt_key=data.get("jwt", {}).get("key", defaults.jwt_key),
            admin_pwd=data.get("login", {}).get("admin", {}).get("pwd", defaults.admin_pwd),
            disabled=data.get("disabled", defaults.disabled),
            external_auth=(
                ExternalAuthConfig.from_dict(data["external_auth"])
                if "external_auth" in data
                else defaults.external_auth
            ),
        )


@dataclass(frozen=True)
class WorkspaceConfig:
    """
    Sub config object dedicated to workspace
    """

    filter_in: list[str] = field(default_factory=lambda: [".*"])
    filter_out: list[str] = field(default_factory=lambda: [])
    groups: list[str] = field(default_factory=lambda: [])
    path: Path = Path()

    @classmethod
    def from_dict(cls, data: JSON) -> "WorkspaceConfig":
        defaults = cls()
        return cls(
            filter_in=data.get("filter_in", defaults.filter_in),
            filter_out=data.get("filter_out", defaults.filter_out),
            groups=data.get("groups", defaults.groups),
            path=Path(data["path"]) if "path" in data else defaults.path,
        )


@dataclass(frozen=True)
class DbConfig:
    """
    Sub config object dedicated to db
    """

    db_url: str = ""
    db_admin_url: str | None = None
    db_connect_timeout: int = 10
    pool_recycle: int | None = None
    pool_pre_ping: bool = False
    pool_use_null: bool = False
    pool_max_overflow: int = 10
    pool_size: int = 5
    pool_use_lifo: bool = False

    @classmethod
    def from_dict(cls, data: JSON) -> "DbConfig":
        defaults = cls()
        return cls(
            db_admin_url=data.get("admin_url", defaults.db_admin_url),
            db_url=data.get("url", defaults.db_url),
            db_connect_timeout=data.get("db_connect_timeout", defaults.db_connect_timeout),
            pool_recycle=data.get("pool_recycle", defaults.pool_recycle),
            pool_pre_ping=data.get("pool_pre_ping", defaults.pool_pre_ping),
            pool_use_null=data.get("pool_use_null", defaults.pool_use_null),
            pool_max_overflow=data.get("pool_max_overflow", defaults.pool_max_overflow),
            pool_size=data.get("pool_size", defaults.pool_size),
            pool_use_lifo=data.get("pool_use_lifo", defaults.pool_use_lifo),
        )


@dataclass(frozen=True)
class V2OutputStorageConfig:
    """
    Configuration for "new style" internal output storage
    """

    enable: bool = False
    archive_dir: Path = Path("./output-archives")
    variables_dir: Path = Path("./output-variables")

    @classmethod
    def from_dict(cls, data: JSON) -> "V2OutputStorageConfig":
        defaults = cls()
        return V2OutputStorageConfig(
            enable=data.get("enable", defaults.enable),
            archive_dir=Path(data.get("archive_dir", str(defaults.archive_dir))),
            variables_dir=Path(data.get("variables_dir", str(defaults.variables_dir))),
        )


@dataclass(frozen=True)
class OutsideStudyFileOutputStorageConfig:
    """
    Configuration for output storage in a single dir for all studies
    """

    storage_dir: Path = Path("./outputs")

    @classmethod
    def from_dict(cls, data: JSON) -> "OutsideStudyFileOutputStorageConfig":
        defaults = cls()
        return OutsideStudyFileOutputStorageConfig(storage_dir=Path(data.get("storage_dir", str(defaults.storage_dir))))


@dataclass(frozen=True)
class OutputStorageConfig:
    """Configuration for output storage"""

    v2: V2OutputStorageConfig = V2OutputStorageConfig()
    outside_study: OutsideStudyFileOutputStorageConfig = OutsideStudyFileOutputStorageConfig()

    default_storage_type: OutputStorageType = OutputStorageType.IN_STUDY_FILE_TREE

    @classmethod
    def from_dict(cls, data: JSON) -> "OutputStorageConfig":
        defaults = cls()
        config = cls(
            v2=V2OutputStorageConfig.from_dict(data.get("v2", {})),
            outside_study=OutsideStudyFileOutputStorageConfig.from_dict(data.get("outside_study", {})),
            default_storage_type=OutputStorageType(data.get("default_storage_type", defaults.default_storage_type)),
        )
        if config.default_storage_type == OutputStorageType.V2 and not config.v2.enable:
            raise ValueError("You cannot set v2 storage as your default storage and not enable it")
        return config


@dataclass(frozen=True)
class StudyStorageConfig:
    """
    Sub config object dedicated to study storage configuration (from study.storage in YAML)
    """

    database_mode_enabled: bool = False

    @classmethod
    def from_dict(cls, data: JSON) -> "StudyStorageConfig":
        defaults = cls()
        return cls(
            database_mode_enabled=data.get("database_mode_enabled", defaults.database_mode_enabled),
        )


@dataclass(frozen=True)
class StorageConfig:
    """
    Sub config object dedicated to study module
    """

    matrixstore: Path = Path("./matrixstore")
    archive_dir: Path = Path("./archives")
    archive_format: ArchiveFormat = ArchiveFormat.ZIP
    tmp_dir: Path = Path(tempfile.gettempdir())
    workspaces: dict[str, WorkspaceConfig] = field(default_factory=dict)
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
    study_storage: StudyStorageConfig = StudyStorageConfig()
    output: OutputStorageConfig = OutputStorageConfig()

    @classmethod
    def from_dict(cls, data: JSON, desktop_mode: bool = False) -> "StorageConfig":
        if data.get("auto_archive_sleeping_time") and data.get("auto_archive_cron"):
            raise ValueError("auto_archive_sleeping_time and auto_archive_cron cannot be used together")
        defaults = cls()
        workspaces = (
            {key: WorkspaceConfig.from_dict(value) for key, value in data["workspaces"].items()}
            if "workspaces" in data
            else defaults.workspaces
        )
        cls.validate_workspaces(workspaces, desktop_mode)
        if desktop_mode:
            workspaces = {**workspaces, **cls.system_workspaces()}
        return cls(
            matrixstore=Path(data["matrixstore"]) if "matrixstore" in data else defaults.matrixstore,
            archive_dir=Path(data["archive_dir"]) if "archive_dir" in data else defaults.archive_dir,
            archive_format=(
                ArchiveFormat(data["archive_format"]) if "archive_format" in data else defaults.archive_format
            ),
            tmp_dir=Path(data["tmp_dir"]) if "tmp_dir" in data else defaults.tmp_dir,
            workspaces=workspaces,
            allow_deletion=data.get("allow_deletion", defaults.allow_deletion),
            watcher_lock=data.get("watcher_lock", defaults.watcher_lock),
            watcher_lock_delay=data.get("watcher_lock_delay", defaults.watcher_lock_delay),
            download_default_expiration_timeout_minutes=(
                data.get(
                    "download_default_expiration_timeout_minutes",
                    defaults.download_default_expiration_timeout_minutes,
                )
            ),
            matrix_gc_sleeping_time=data.get("matrix_gc_sleeping_time", defaults.matrix_gc_sleeping_time),
            matrix_gc_dry_run=data.get("matrix_gc_dry_run", defaults.matrix_gc_dry_run),
            matrix_gc_retention_time=data.get("matrix_gc_retention_time", defaults.matrix_gc_retention_time),
            auto_archive_threshold_days=data.get("auto_archive_threshold_days", defaults.auto_archive_threshold_days),
            auto_archive_dry_run=data.get("auto_archive_dry_run", defaults.auto_archive_dry_run),
            auto_archive_sleeping_time=data.get("auto_archive_sleeping_time", defaults.auto_archive_sleeping_time),
            auto_archive_cron=data.get("auto_archive_cron", defaults.auto_archive_cron),
            snapshot_retention_days=data.get("snapshot_retention_days", defaults.snapshot_retention_days),
            matrixstore_format=InternalMatrixFormat(data.get("matrixstore_format", defaults.matrixstore_format)),
            blobstore=Path(data["blobstore"]) if "blobstore" in data else defaults.blobstore,
            blob_gc_sleeping_time=data.get("blob_gc_sleeping_time", defaults.blob_gc_sleeping_time),
            blob_gc_dry_run=data.get("blob_gc_dry_run", defaults.blob_gc_dry_run),
            variable_view_gc_sleeping_time=data.get(
                "variable_view_gc_sleeping_time", defaults.variable_view_gc_sleeping_time
            ),
            variable_view_gc_dry_run=data.get("variable_view_gc_dry_run", defaults.variable_view_gc_dry_run),
            variable_view_gc_retention_days=data.get(
                "variable_view_gc_retention_days", defaults.variable_view_gc_retention_days
            ),
            watcher_scan_sleeping_time=data.get("watcher_scan_sleeping_time", defaults.watcher_scan_sleeping_time),
            watcher_scan_dry_run=data.get("watcher_scan_dry_run", defaults.watcher_scan_dry_run),
            tasks_gc_retention_days=data.get("tasks_gc_retention_days", defaults.tasks_gc_retention_days),
            study_storage=StudyStorageConfig.from_dict(data.get("study", {}).get("storage", {})),
            output=OutputStorageConfig.from_dict(data["output"]) if "output" in data else defaults.output,
        )

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


@dataclass(frozen=True)
class NbCoresConfig:
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

    def __post_init__(self) -> None:
        """validation of CPU configuration"""
        if 1 <= self.min <= self.default <= self.max:
            return
        msg = f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}"
        raise ValueError(msg)


@dataclass(frozen=True)
class TimeLimitConfig:
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

    def __post_init__(self) -> None:
        """validation of CPU configuration"""
        if 1 <= self.min <= self.default <= self.max:
            return
        msg = f"Invalid configuration: 1 <= {self.min=} <= {self.default=} <= {self.max=}"
        raise ValueError(msg)


@dataclass(frozen=True)
class LocalConfig:
    """Sub config object dedicated to launcher module (local)"""

    id: str
    name: str
    type: ClassVar[LauncherType] = LauncherType.LOCAL
    binaries: dict[SolverVersion, Path] = field(default_factory=dict)
    enable_nb_cores_detection: bool = True
    nb_cores: NbCoresConfig = NbCoresConfig()
    time_limit: TimeLimitConfig = TimeLimitConfig()
    xpress_dir: str | None = None
    local_workspace: Path = Path("./local_workspace")

    @classmethod
    def from_dict(cls, data: JSON) -> "LocalConfig":
        """
        Creates an instance of LocalConfig from a data dictionary
        Args:
            data: Parse config from dict.
        Returns: object NbCoresConfig
        """
        binaries = {SolverVersion.parse(str(k)): Path(v) for k, v in data.get("binaries", {}).items()}
        enable_nb_cores_detection = data.get("enable_nb_cores_detection", True)
        nb_cores = data.get("nb_cores", asdict(NbCoresConfig()))
        if enable_nb_cores_detection:
            nb_cores.update(cls._autodetect_nb_cores())
        xpress_dir = data.get("xpress_dir")
        local_workspace = Path(data["local_workspace"]) if "local_workspace" in data else Path("./local_workspace")
        return cls(
            id=data["id"],
            name=data["name"],
            binaries=binaries,
            enable_nb_cores_detection=enable_nb_cores_detection,
            nb_cores=NbCoresConfig(**nb_cores),
            xpress_dir=xpress_dir,
            local_workspace=local_workspace,
        )

    @classmethod
    def _autodetect_nb_cores(cls) -> dict[str, int]:
        """
        Automatically detects the number of cores available on the user's machine
        Returns: Instance of NbCoresConfig
        """
        min_cpu = cls.nb_cores.min
        max_cpu = multiprocessing.cpu_count()
        default = max(min_cpu, max_cpu - 2)
        return {"min": min_cpu, "max": max_cpu, "default": default}


@dataclass(frozen=True)
class SlurmConfig:
    """
    Sub config object dedicated to launcher module (slurm)
    """

    id: str
    name: str
    type: ClassVar[LauncherType] = LauncherType.SLURM
    local_workspace: Path = Path()
    username: str = ""
    hostname: str = ""
    port: int = 0
    private_key_file: Path = Path()
    key_password: str = ""
    password: str = ""
    default_wait_time: int = 0
    time_limit: TimeLimitConfig = TimeLimitConfig()
    nb_cores: NbCoresConfig = NbCoresConfig()
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    partition: str = ""
    max_cores: int = 64
    antares_versions_on_remote_server: list[SolverVersion] = field(default_factory=list)
    enable_nb_cores_detection: bool = False

    @classmethod
    def from_dict(cls, data: JSON) -> "SlurmConfig":
        """
        Creates an instance of SlurmConfig from a data dictionary

        Args:
             data: Parsed config from dict.
        Returns: object SlurmConfig
        """
        enable_nb_cores_detection = data.get("enable_nb_cores_detection", False)
        nb_cores = data.get("nb_cores", asdict(NbCoresConfig()))
        if "default_n_cpu" in data:
            # Use the old way to configure the NB cores for backward compatibility
            nb_cores["default"] = int(data["default_n_cpu"])
            nb_cores["min"] = min(nb_cores["min"], nb_cores["default"])
            nb_cores["max"] = max(nb_cores["max"], nb_cores["default"])
        if enable_nb_cores_detection:
            nb_cores.update(cls._autodetect_nb_cores())
        # In the configuration file, the default time limit is in seconds, so we convert it to hours
        max_time_limit = data.get("default_time_limit", TimeLimitConfig().max * 3600) // 3600
        time_limit = TimeLimitConfig(min=1, default=max_time_limit, max=max_time_limit)
        antares_versions_as_str = data.get("antares_versions_on_remote_server", [])
        antares_versions_on_remote_server = [SolverVersion.parse(str(v)) for v in antares_versions_as_str]
        return cls(
            id=data["id"],
            name=data["name"],
            local_workspace=Path(data.get("local_workspace", Path())),
            username=data.get("username", ""),
            hostname=data.get("hostname", ""),
            port=data.get("port", 0),
            private_key_file=data.get("private_key_file", Path()),
            key_password=data.get("key_password", ""),
            password=data.get("password", ""),
            default_wait_time=data.get("default_wait_time", 0),
            time_limit=time_limit,
            default_json_db_name=data.get("default_json_db_name", ""),
            slurm_script_path=data.get("slurm_script_path", ""),
            partition=data.get("partition", ""),
            antares_versions_on_remote_server=antares_versions_on_remote_server,
            max_cores=data.get("max_cores", 64),
            enable_nb_cores_detection=enable_nb_cores_detection,
            nb_cores=NbCoresConfig(**nb_cores),
        )

    @classmethod
    def _autodetect_nb_cores(cls) -> dict[str, int]:
        raise NotImplementedError("NB Cores auto-detection is not implemented for SLURM server")


class InvalidConfigurationError(Exception):
    """
    Exception raised when an attempt is made to retrieve a property
    of a launcher that doesn't exist in the configuration.
    """

    def __init__(self, launcher: str):
        msg = f"Configuration is not available for the '{launcher}' launcher"
        super().__init__(msg)


@dataclass(frozen=True)
class LauncherConfig:
    """
    Sub config object dedicated to launcher module
    """

    default: str = "local"
    configs: list[LocalConfig | SlurmConfig] | None = None
    batch_size: int = 9999

    @classmethod
    def from_dict(cls, data: JSON) -> "LauncherConfig":
        launchers: list[LocalConfig | SlurmConfig] = []
        defaults = cls()
        default = data.get("default", cls.default)
        batch_size = data.get("batch_size", defaults.batch_size)
        for launcher in data["launchers"]:
            match launcher["type"]:
                case LauncherType.LOCAL:
                    launchers.append(LocalConfig.from_dict(launcher))
                case LauncherType.SLURM:
                    launchers.append(SlurmConfig.from_dict(launcher))
                case _:
                    raise InvalidConfigurationError(f"Unknown launcher type: {launcher['type']}")

        if not any(launcher.id == default for launcher in launchers):
            raise InvalidConfigurationError(f"Default launcher id '{default}' not found in launcher configs")

        return cls(
            default=default,
            configs=launchers,
            batch_size=batch_size,
        )

    def get_slurm_configs(self) -> list[SlurmConfig]:
        return [cfg for cfg in self.configs or [] if isinstance(cfg, SlurmConfig)]


@dataclass(frozen=True)
class LoggingConfig:
    """
    Sub config object dedicated to logging
    """

    logfile: Path | None = None
    json: bool = False
    level: str = "INFO"

    @classmethod
    def from_dict(cls, data: JSON) -> "LoggingConfig":
        defaults = cls()
        return cls(
            logfile=Path(data["logfile"]) if "logfile" in data else defaults.logfile,
            json=data.get("json", defaults.json),
            level=data.get("level", defaults.level),
        )


@dataclass(frozen=True)
class RedisConfig:
    """
    Sub config object dedicated to redis
    """

    host: str = "localhost"
    port: int = 6379
    password: str | None = None

    @classmethod
    def from_dict(cls, data: JSON) -> "RedisConfig":
        defaults = cls()
        return cls(
            host=data.get("host", defaults.host),
            port=data.get("port", defaults.port),
            password=data.get("password", defaults.password),
        )


@dataclass(frozen=True)
class EventBusConfig:
    """
    Sub config object dedicated to eventbus module
    """

    # noinspection PyUnusedLocal
    @classmethod
    def from_dict(cls, data: JSON) -> "EventBusConfig":
        return cls()


@dataclass(frozen=True)
class CacheConfig:
    """
    Sub config object dedicated to cache module
    """

    checker_delay: float = 0.2  # in seconds

    @classmethod
    def from_dict(cls, data: JSON) -> "CacheConfig":
        defaults = cls()
        return cls(
            checker_delay=data.get("checker_delay", defaults.checker_delay),
        )


@dataclass(frozen=True)
class RemoteWorkerConfig:
    name: str
    queues: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JSON) -> "RemoteWorkerConfig":
        defaults = cls(name="")  # `name` is mandatory
        return cls(
            name=data["name"],
            queues=data.get("queues", defaults.queues),
        )


@dataclass(frozen=True)
class TaskConfig:
    """
    Sub config object dedicated to the task module
    """

    max_workers: int = 5
    remote_workers: list[RemoteWorkerConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JSON) -> "TaskConfig":
        defaults = cls()
        remote_workers = (
            [RemoteWorkerConfig.from_dict(d) for d in data["remote_workers"]]
            if "remote_workers" in data
            else defaults.remote_workers
        )
        return cls(
            max_workers=data.get("max_workers", defaults.max_workers),
            remote_workers=remote_workers,
        )


@dataclass(frozen=True)
class ServerConfig:
    """
    Sub config object dedicated to the server
    """

    worker_threadpool_size: int = 5
    services: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JSON) -> "ServerConfig":
        defaults = cls()
        return cls(
            worker_threadpool_size=data.get("worker_threadpool_size", defaults.worker_threadpool_size),
            services=data.get("services", defaults.services),
        )


@dataclass(frozen=True)
class PrometheusConfig:
    """
    Sub config object dedicated to prometheus metrics

    Attributes:
        multiprocess: if True, metrics of workers will be aggregated before exposition.
                      Environment variable `PROMETHEUS_MULTIPROC_DIR` must be set.
    """

    multiprocess: bool = False

    @classmethod
    def from_dict(cls, data: JSON) -> "PrometheusConfig":
        return cls(multiprocess=bool(data["multiprocess"]))


@dataclass(frozen=True)
class MetricsConfig:
    """
    Sub config object dedicated to metrics

    Attributes:
        prometheus: if not None, metrics will be exposed in prometheus format
    """

    prometheus: PrometheusConfig | None = None

    @classmethod
    def from_dict(cls, data: JSON) -> "MetricsConfig":
        return cls(prometheus=PrometheusConfig.from_dict(data["prometheus"]) if "prometheus" in data else None)


@dataclass(frozen=True)
class CeleryConfig:
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

    @classmethod
    def from_dict(cls, data: JSON, redis_config: RedisConfig | None = None) -> "CeleryConfig":
        defaults = cls()

        if redis_config:
            redis_url = cls._build_redis_url(redis_config, cls.REDIS_DB)
        else:
            redis_url = ""

        return cls(
            broker_url=data.get("broker_url", redis_url),
            result_backend=data.get("result_backend", redis_url),
            result_expires=data.get("result_expires", defaults.result_expires),
        )


@dataclass(frozen=True)
class Config:
    """
    Root server config
    """

    server: ServerConfig = ServerConfig()
    security: SecurityConfig = SecurityConfig()
    storage: StorageConfig = StorageConfig()
    launcher: LauncherConfig = LauncherConfig()
    db: DbConfig = DbConfig()
    logging: LoggingConfig = LoggingConfig()
    debug: bool = True
    resources_path: Path = Path()
    redis: RedisConfig | None = None
    eventbus: EventBusConfig = EventBusConfig()
    cache: CacheConfig = CacheConfig()
    tasks: TaskConfig = TaskConfig()
    metrics: MetricsConfig = MetricsConfig()
    celery: CeleryConfig = CeleryConfig()
    root_path: str = ""
    api_prefix: str = ""
    desktop_mode: bool = False

    @classmethod
    def from_dict(cls, data: JSON) -> "Config":
        defaults = cls()
        desktop_mode = data.get("desktop_mode", defaults.desktop_mode)
        storage_config = (
            StorageConfig.from_dict(data["storage"], desktop_mode=desktop_mode)
            if "storage" in data
            else defaults.storage
        )
        redis_config = RedisConfig.from_dict(data["redis"]) if "redis" in data else defaults.redis
        return cls(
            server=ServerConfig.from_dict(data["server"]) if "server" in data else defaults.server,
            security=SecurityConfig.from_dict(data["security"]) if "security" in data else defaults.security,
            storage=storage_config,
            launcher=LauncherConfig.from_dict(data["launcher"]) if "launcher" in data else defaults.launcher,
            db=DbConfig.from_dict(data["db"]) if "db" in data else defaults.db,
            logging=LoggingConfig.from_dict(data["logging"]) if "logging" in data else defaults.logging,
            debug=data.get("debug", defaults.debug),
            resources_path=data["resources_path"] if "resources_path" in data else defaults.resources_path,
            redis=redis_config,
            eventbus=EventBusConfig.from_dict(data["eventbus"]) if "eventbus" in data else defaults.eventbus,
            cache=CacheConfig.from_dict(data["cache"]) if "cache" in data else defaults.cache,
            tasks=TaskConfig.from_dict(data["tasks"]) if "tasks" in data else defaults.tasks,
            celery=CeleryConfig.from_dict(data.get("celery", {}), redis_config=redis_config),
            root_path=data.get("root_path", defaults.root_path),
            api_prefix=data.get("api_prefix", defaults.api_prefix),
            desktop_mode=desktop_mode,
            metrics=MetricsConfig.from_dict(data["metrics"]) if "metrics" in data else MetricsConfig(),
        )

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
        return cls.from_dict(data)

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
