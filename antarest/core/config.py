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

import multiprocessing
import tempfile
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Dict, List, Optional, cast

import pandas as pd
import yaml

from antarest.core.model import JSON
from antarest.core.roles import RoleType

DEFAULT_WORKSPACE_NAME = "default"


class Launcher(StrEnum):
    SLURM = "slurm"
    LOCAL = "local"
    DEFAULT = "default"


class InternalMatrixFormat(StrEnum):
    TSV = "tsv"
    HDF = "hdf"
    PARQUET = "parquet"
    FEATHER = "feather"

    def load_matrix(self, path: Path) -> pd.DataFrame:
        if path.stat().st_size == 0:
            return pd.DataFrame()
        if self == InternalMatrixFormat.TSV:
            # The legacy format is TSV, so we have to handle both cases
            # To know if we're opening a legacy matrix or not we have to seek the first bytes of the file
            # Legacy
            header = None
            index_col = None
            with open(path, "r") as f:
                if f.read(1) == "\t":
                    # New format
                    header = 0
                    index_col = 0
            df = pd.read_csv(path, sep="\t", index_col=index_col, header=header)
            # Specific treatment on columns to fit with other formats
            length_range = range(len(df.columns))
            if list(df.columns) == [str(k) for k in length_range]:
                df.columns = pd.Index(length_range)  # type: ignore
            return df
        elif self == InternalMatrixFormat.HDF:
            return cast(pd.DataFrame, pd.read_hdf(path))
        elif self == InternalMatrixFormat.PARQUET:
            return pd.read_parquet(path)
        elif self == InternalMatrixFormat.FEATHER:
            return pd.read_feather(path)
        else:
            raise NotImplementedError(f"Internal matrix format '{self}' is not implemented")

    def save_matrix(self, dataframe: pd.DataFrame, path: Path) -> None:
        if self == InternalMatrixFormat.TSV:
            dataframe.to_csv(path, sep="\t", float_format="%.6f")
        elif self == InternalMatrixFormat.HDF:
            dataframe.to_hdf(str(path), key="data")
        elif self == InternalMatrixFormat.PARQUET:
            dataframe.to_parquet(path, compression=None)
        elif self == InternalMatrixFormat.FEATHER:
            dataframe.to_feather(path)
        else:
            raise NotImplementedError(f"Internal matrix format '{self}' is not implemented")


@dataclass(frozen=True)
class ExternalAuthConfig:
    """
    Sub config object dedicated to external auth service
    """

    url: Optional[str] = None
    default_group_role: RoleType = RoleType.READER
    add_ext_groups: bool = False
    group_mapping: Dict[str, str] = field(default_factory=dict)

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

    filter_in: List[str] = field(default_factory=lambda: [".*"])
    filter_out: List[str] = field(default_factory=lambda: [])
    groups: List[str] = field(default_factory=lambda: [])
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
    db_admin_url: Optional[str] = None
    db_connect_timeout: int = 10
    pool_recycle: Optional[int] = None
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
class StorageConfig:
    """
    Sub config object dedicated to study module
    """

    matrixstore: Path = Path("./matrixstore")
    archive_dir: Path = Path("./archives")
    tmp_dir: Path = Path(tempfile.gettempdir())
    workspaces: Dict[str, WorkspaceConfig] = field(default_factory=dict)
    allow_deletion: bool = False
    watcher_lock: bool = True
    watcher_lock_delay: int = 10
    download_default_expiration_timeout_minutes: int = 1440
    matrix_gc_sleeping_time: int = 3600
    matrix_gc_dry_run: bool = False
    auto_archive_threshold_days: int = 60
    auto_archive_dry_run: bool = False
    auto_archive_sleeping_time: int = 3600
    auto_archive_max_parallel: int = 5
    snapshot_retention_days: int = 7
    matrixstore_format: InternalMatrixFormat = InternalMatrixFormat.TSV

    @classmethod
    def from_dict(cls, data: JSON) -> "StorageConfig":
        defaults = cls()
        workspaces = (
            {key: WorkspaceConfig.from_dict(value) for key, value in data["workspaces"].items()}
            if "workspaces" in data
            else defaults.workspaces
        )

        cls._validate_workspaces(data, workspaces)
        return cls(
            matrixstore=Path(data["matrixstore"]) if "matrixstore" in data else defaults.matrixstore,
            archive_dir=Path(data["archive_dir"]) if "archive_dir" in data else defaults.archive_dir,
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
            auto_archive_threshold_days=data.get("auto_archive_threshold_days", defaults.auto_archive_threshold_days),
            auto_archive_dry_run=data.get("auto_archive_dry_run", defaults.auto_archive_dry_run),
            auto_archive_sleeping_time=data.get("auto_archive_sleeping_time", defaults.auto_archive_sleeping_time),
            auto_archive_max_parallel=data.get("auto_archive_max_parallel", defaults.auto_archive_max_parallel),
            snapshot_retention_days=data.get("snapshot_retention_days", defaults.snapshot_retention_days),
            matrixstore_format=InternalMatrixFormat(data.get("matrixstore_format", defaults.matrixstore_format)),
        )

    @classmethod
    def _validate_workspaces(cls, config_as_json: JSON, workspaces: Dict[str, WorkspaceConfig]) -> None:
        """
        Validate that no two workspaces have overlapping paths.
        """
        workspace_name_by_path = [(config.path, name) for name, config in workspaces.items()]
        for path, name in workspace_name_by_path:
            for path2, name2 in workspace_name_by_path:
                if name != name2 and path.is_relative_to(path2):
                    raise ValueError(
                        f"Overlapping workspace paths found: '{name}' and '{name2}' '{path}' is relative to '{path2}' "
                    )


@dataclass(frozen=True)
class NbCoresConfig:
    """
    The NBCoresConfig class is designed to manage the configuration of the number of CPU cores
    """

    min: int = 1
    default: int = 22
    max: int = 24

    def to_json(self) -> Dict[str, int]:
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

    def to_json(self) -> Dict[str, int]:
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

    binaries: Dict[str, Path] = field(default_factory=dict)
    enable_nb_cores_detection: bool = True
    nb_cores: NbCoresConfig = NbCoresConfig()
    time_limit: TimeLimitConfig = TimeLimitConfig()
    xpress_dir: Optional[str] = None
    local_workspace: Path = Path("./local_workspace")

    @classmethod
    def from_dict(cls, data: JSON) -> "LocalConfig":
        """
        Creates an instance of LocalConfig from a data dictionary
        Args:
            data: Parse config from dict.
        Returns: object NbCoresConfig
        """
        defaults = cls()
        binaries = data.get("binaries", defaults.binaries)
        enable_nb_cores_detection = data.get("enable_nb_cores_detection", defaults.enable_nb_cores_detection)
        nb_cores = data.get("nb_cores", asdict(defaults.nb_cores))
        if enable_nb_cores_detection:
            nb_cores.update(cls._autodetect_nb_cores())
        xpress_dir = data.get("xpress_dir", defaults.xpress_dir)
        local_workspace = Path(data["local_workspace"]) if "local_workspace" in data else defaults.local_workspace
        return cls(
            binaries={str(v): Path(p) for v, p in binaries.items()},
            enable_nb_cores_detection=enable_nb_cores_detection,
            nb_cores=NbCoresConfig(**nb_cores),
            xpress_dir=xpress_dir,
            local_workspace=local_workspace,
        )

    @classmethod
    def _autodetect_nb_cores(cls) -> Dict[str, int]:
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

    local_workspace: Path = Path()
    username: str = ""
    hostname: str = ""
    port: int = 0
    private_key_file: Path = Path()
    key_password: str = ""
    password: str = ""
    default_wait_time: int = 0
    time_limit: TimeLimitConfig = TimeLimitConfig()
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    partition: str = ""
    max_cores: int = 64
    antares_versions_on_remote_server: List[str] = field(default_factory=list)
    enable_nb_cores_detection: bool = False
    nb_cores: NbCoresConfig = NbCoresConfig()

    @classmethod
    def from_dict(cls, data: JSON) -> "SlurmConfig":
        """
        Creates an instance of SlurmConfig from a data dictionary

        Args:
             data: Parsed config from dict.
        Returns: object SlurmConfig
        """
        defaults = cls()
        enable_nb_cores_detection = data.get("enable_nb_cores_detection", defaults.enable_nb_cores_detection)
        nb_cores = data.get("nb_cores", asdict(defaults.nb_cores))
        if "default_n_cpu" in data:
            # Use the old way to configure the NB cores for backward compatibility
            nb_cores["default"] = int(data["default_n_cpu"])
            nb_cores["min"] = min(nb_cores["min"], nb_cores["default"])
            nb_cores["max"] = max(nb_cores["max"], nb_cores["default"])
        if enable_nb_cores_detection:
            nb_cores.update(cls._autodetect_nb_cores())
        # In the configuration file, the default time limit is in seconds, so we convert it to hours
        max_time_limit = data.get("default_time_limit", defaults.time_limit.max * 3600) // 3600
        time_limit = TimeLimitConfig(min=1, default=max_time_limit, max=max_time_limit)
        return cls(
            local_workspace=Path(data.get("local_workspace", defaults.local_workspace)),
            username=data.get("username", defaults.username),
            hostname=data.get("hostname", defaults.hostname),
            port=data.get("port", defaults.port),
            private_key_file=data.get("private_key_file", defaults.private_key_file),
            key_password=data.get("key_password", defaults.key_password),
            password=data.get("password", defaults.password),
            default_wait_time=data.get("default_wait_time", defaults.default_wait_time),
            time_limit=time_limit,
            default_json_db_name=data.get("default_json_db_name", defaults.default_json_db_name),
            slurm_script_path=data.get("slurm_script_path", defaults.slurm_script_path),
            partition=data.get("partition", defaults.partition),
            antares_versions_on_remote_server=data.get(
                "antares_versions_on_remote_server",
                defaults.antares_versions_on_remote_server,
            ),
            max_cores=data.get("max_cores", defaults.max_cores),
            enable_nb_cores_detection=enable_nb_cores_detection,
            nb_cores=NbCoresConfig(**nb_cores),
        )

    @classmethod
    def _autodetect_nb_cores(cls) -> Dict[str, int]:
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
    local: Optional[LocalConfig] = None
    slurm: Optional[SlurmConfig] = None
    batch_size: int = 9999

    @classmethod
    def from_dict(cls, data: JSON) -> "LauncherConfig":
        defaults = cls()
        default = data.get("default", cls.default)
        local = LocalConfig.from_dict(data["local"]) if "local" in data else defaults.local
        slurm = SlurmConfig.from_dict(data["slurm"]) if "slurm" in data else defaults.slurm
        batch_size = data.get("batch_size", defaults.batch_size)
        return cls(
            default=default,
            local=local,
            slurm=slurm,
            batch_size=batch_size,
        )

    def __post_init__(self) -> None:
        possible = {"local", "slurm"}
        if self.default in possible:
            return
        msg = f"Invalid configuration: {self.default=} must be one of {possible!r}"
        raise ValueError(msg)

    def get_nb_cores(self, launcher: Launcher) -> "NbCoresConfig":
        """
        Retrieve the number of cores configuration for a given launcher: "local" or "slurm".
        If "default" is specified, retrieve the configuration of the default launcher.

        Args:
            launcher: type of launcher "local", "slurm" or "default".

        Returns:
            Number of cores of the given launcher.

        Raises:
            InvalidConfigurationError: Exception raised when an attempt is made to retrieve
                the number of cores of a launcher that doesn't exist in the configuration.
        """
        config_map = {"local": self.local, "slurm": self.slurm}
        config_map["default"] = config_map[self.default]
        launcher_config = config_map.get(launcher.value)
        if launcher_config is None:
            raise InvalidConfigurationError(launcher.value)
        return launcher_config.nb_cores

    def get_time_limit(self, launcher: Launcher) -> TimeLimitConfig:
        """
        Retrieve the time limit for a job of the given launcher: "local" or "slurm".
        If "default" is specified, retrieve the configuration of the default launcher.

        Args:
            launcher: type of launcher "local", "slurm" or "default".

        Returns:
            Time limit for a job of the given launcher (in seconds).

        Raises:
            InvalidConfigurationError: Exception raised when an attempt is made to retrieve
                a property of a launcher that doesn't exist in the configuration.
        """
        config_map = {"local": self.local, "slurm": self.slurm}
        config_map["default"] = config_map[self.default]
        launcher_config = config_map.get(launcher.value)
        if launcher_config is None:
            raise InvalidConfigurationError(launcher)
        return launcher_config.time_limit


@dataclass(frozen=True)
class LoggingConfig:
    """
    Sub config object dedicated to logging
    """

    logfile: Optional[Path] = None
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
    password: Optional[str] = None

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
    queues: List[str] = field(default_factory=list)

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
    remote_workers: List[RemoteWorkerConfig] = field(default_factory=list)

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
    services: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: JSON) -> "ServerConfig":
        defaults = cls()
        return cls(
            worker_threadpool_size=data.get("worker_threadpool_size", defaults.worker_threadpool_size),
            services=data.get("services", defaults.services),
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
    redis: Optional[RedisConfig] = None
    eventbus: EventBusConfig = EventBusConfig()
    cache: CacheConfig = CacheConfig()
    tasks: TaskConfig = TaskConfig()
    root_path: str = ""
    api_prefix: str = ""

    @classmethod
    def from_dict(cls, data: JSON) -> "Config":
        defaults = cls()
        return cls(
            server=ServerConfig.from_dict(data["server"]) if "server" in data else defaults.server,
            security=SecurityConfig.from_dict(data["security"]) if "security" in data else defaults.security,
            storage=StorageConfig.from_dict(data["storage"]) if "storage" in data else defaults.storage,
            launcher=LauncherConfig.from_dict(data["launcher"]) if "launcher" in data else defaults.launcher,
            db=DbConfig.from_dict(data["db"]) if "db" in data else defaults.db,
            logging=LoggingConfig.from_dict(data["logging"]) if "logging" in data else defaults.logging,
            debug=data.get("debug", defaults.debug),
            resources_path=data["resources_path"] if "resources_path" in data else defaults.resources_path,
            redis=RedisConfig.from_dict(data["redis"]) if "redis" in data else defaults.redis,
            eventbus=EventBusConfig.from_dict(data["eventbus"]) if "eventbus" in data else defaults.eventbus,
            cache=CacheConfig.from_dict(data["cache"]) if "cache" in data else defaults.cache,
            tasks=TaskConfig.from_dict(data["tasks"]) if "tasks" in data else defaults.tasks,
            root_path=data.get("root_path", defaults.root_path),
            api_prefix=data.get("api_prefix", defaults.api_prefix),
        )

    @classmethod
    def from_yaml_file(cls, file: Path, res: Optional[Path] = None) -> "Config":
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
