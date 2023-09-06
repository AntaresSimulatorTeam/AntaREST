import logging
import multiprocessing
import os
import tempfile
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from fastapi import HTTPException

from antarest.core.model import JSON
from antarest.core.roles import RoleType

logger = logging.getLogger(__name__)


class LauncherConfNotAvailableException(HTTPException):
    """
    This exception  is raised in order to  detect errors from conf.py
    """

    def __init__(self, msg_error: str):
        super(LauncherConfNotAvailableException, self).__init__(HTTPStatus.BAD_REQUEST, msg_error)


@dataclass(frozen=True)
class ExternalAuthConfig:
    """
    Sub config object dedicated to external auth service
    """

    url: Optional[str] = None
    default_group_role: RoleType = RoleType.READER
    add_ext_groups: bool = False
    group_mapping: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: JSON) -> "ExternalAuthConfig":
        return ExternalAuthConfig(
            url=data.get("url", None),
            default_group_role=RoleType(data.get("default_group_role", RoleType.READER.value)),
            add_ext_groups=data.get("add_ext_groups", False),
            group_mapping=data.get("group_mapping", {}),
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

    @staticmethod
    def from_dict(data: JSON) -> "SecurityConfig":
        return SecurityConfig(
            jwt_key=data.get("jwt", {}).get("key", ""),
            admin_pwd=data.get("login", {}).get("admin", {}).get("pwd", ""),
            disabled=data.get("disabled", False),
            external_auth=ExternalAuthConfig.from_dict(data.get("external_auth", {})),
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

    @staticmethod
    def from_dict(data: JSON) -> "WorkspaceConfig":
        return WorkspaceConfig(
            path=Path(data["path"]),
            groups=data.get("groups", []),
            filter_in=data.get("filter_in", [".*"]),
            filter_out=data.get("filter_out", []),
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

    @staticmethod
    def from_dict(data: JSON) -> "DbConfig":
        return DbConfig(
            db_admin_url=data.get("admin_url", None),
            db_url=data.get("url", ""),
            db_connect_timeout=data.get("db_connect_timeout", 10),
            pool_recycle=data.get("pool_recycle", None),
            pool_pre_ping=data.get("pool_pre_ping", False),
            pool_use_null=data.get("pool_use_null", False),
            pool_max_overflow=data.get("pool_max_overflow", 10),
            pool_size=data.get("pool_size", 5),
            pool_use_lifo=data.get("pool_use_lifo", False),
        )


@dataclass(frozen=True)
class StorageConfig:
    """
    Sub config object dedicated to study module
    """

    matrixstore: Path = Path("./matrixstore")
    archive_dir: Path = Path("./archives")
    tmp_dir: Path = Path(tempfile.gettempdir())
    workspaces: Dict[str, WorkspaceConfig] = field(default_factory=lambda: {})
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

    @staticmethod
    def from_dict(data: JSON) -> "StorageConfig":
        return StorageConfig(
            tmp_dir=Path(data.get("tmp_dir", tempfile.gettempdir())),
            matrixstore=Path(data["matrixstore"]),
            workspaces={n: WorkspaceConfig.from_dict(w) for n, w in data["workspaces"].items()},
            allow_deletion=data.get("allow_deletion", False),
            archive_dir=Path(data["archive_dir"]),
            watcher_lock=data.get("watcher_lock", True),
            watcher_lock_delay=data.get("watcher_lock_delay", 10),
            download_default_expiration_timeout_minutes=data.get("download_default_expiration_timeout_minutes", 1440),
            matrix_gc_sleeping_time=data.get("matrix_gc_sleeping_time", 3600),
            matrix_gc_dry_run=data.get("matrix_gc_dry_run", False),
            auto_archive_threshold_days=data.get("auto_archive_threshold_days", 60),
            auto_archive_dry_run=data.get("auto_archive_dry_run", False),
            auto_archive_sleeping_time=data.get("auto_archive_sleeping_time", 3600),
            auto_archive_max_parallel=data.get("auto_archive_max_parallel", 5),
        )


@dataclass(frozen=True)
class NbCoresConfig:
    """
    The NBCoresConfig class is designed to manage the configuration of the number of CPU cores
    """

    min: int = 1
    default: int = 22
    max: int = 24

    @staticmethod
    def from_dict(data: JSON) -> "NBCoresConfig":
        """
        Creates an instance of NBCoresConfig from a data dictionary
        Args:
            data: Parse config from dict.

        Returns: object NbCoresConfig

        """
        NbCoresConfig.__validate_nb_cores(
            min_cpu=data.get("min", None), max_cpu=data.get("max", None), default=data.get("default", None)
        )
        return NbCoresConfig(min=data.get("min", None), max=data.get("max", None), default=data.get("default", None))

    @staticmethod
    def to_json(min_cpu, max_cpu, default) -> Dict[str, int]:
        """
        Retrieves the number of cores parameters, returning a dictionary containing the values "min"
        (minimum allowed value), "defaultValue" (default value), and "max" (maximum allowed value)
        Args:
            default: default number of core cpu
            max_cpu: minimum number of core cpu
            min_cpu: maximum number of core cpu
        Returns: Dict of core config
        """
        NbCoresConfig.__validate_nb_cores(min_cpu=min_cpu, max_cpu=max_cpu, default=default)
        return {"min": min_cpu, "default": default, "max": max_cpu}

    @staticmethod
    def __post__(self) -> None:
        raise NotImplementedError()

    @staticmethod
    def __validate_nb_cores(min_cpu: int, default: int, max_cpu: int) -> None:
        """
        Validates the number of cores parameters, raising an exception if they are
        invalid (i.e., if 1 ≤ min ≤ default ≤ max is false)
        Args:
            min_cpu: min cpu
            default: default cpu
            max_cpu: max cpu
        Returns:
        """
        msg = ""
        if min_cpu > 1 or min_cpu == 0 or min_cpu > max_cpu:
            msg = f"value min_cpu:{min_cpu} must be equal to 1"
        elif default > max_cpu or default < 1:
            msg = f"{msg} {default}  must be less than max_cpu:{max_cpu} or greater than 1"
        if msg:
            raise LauncherConfNotAvailableException(msg)


@dataclass(frozen=True)
class LocalConfig:
    """Sub config object dedicated to launcher module (local)"""

    binaries: Dict[str, Path] = field(default_factory=dict)
    enable_nb_core_detection: bool = True
    nb_cores: object = NbCoresConfig()

    @staticmethod
    def from_dict(data: JSON) -> Optional["LocalConfig"]:
        return LocalConfig(
            binaries={str(v): Path(p) for v, p in data["binaries"].items()},
        )

    @staticmethod
    def _autodetect_nb_cores() -> object:
        """
        Automatically detects the number of cores available on the user's machine
        Returns: the number of cores configuration for a given solver: "local"
        """
        min_cpu = 1
        info_data = Config.from_yaml_to_dict()
        enable_nb_core_detection = info_data["launcher"]["local"]["enable_nb_cores_detection"]
        if enable_nb_core_detection:
            max_cpu = multiprocessing.cpu_count()
        else:
            raise (
                LauncherConfNotAvailableException("Automatically detects the number of cores available is not active")
            )
        default = max(min_cpu, max_cpu - 2)
        LocalConfig.nb_cores = NbCoresConfig(min=min_cpu, max=max_cpu, default=default)
        return NbCoresConfig().to_json(min_cpu=min_cpu, max_cpu=max_cpu, default=default)


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
    default_time_limit: int = 0
    default_n_cpu: int = 1
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    max_cores: int = 64
    antares_versions_on_remote_server: List[str] = field(default_factory=list)
    enable_nb_core_detection: bool = False
    nb_cores: object = NbCoresConfig()

    @staticmethod
    def from_dict(data: JSON) -> "SlurmConfig":
        if "nb_cores" in data:
            nb_cores = NbCoresConfig.from_dict(data["nb_cores"])
        else:
            nb_cores = NbCoresConfig(min=1, default=data["default_n_cpu"], max=24)
        return SlurmConfig(
            local_workspace=Path(data.get("local_workspace")) if data.get("local_workspace") else None,
            username=data.get("username"),
            hostname=data.get("hostname"),
            port=data.get("port"),
            private_key_file=data.get("private_key_file", None),
            key_password=data.get("key_password", None),
            password=data.get("password", None),
            default_wait_time=data.get("default_wait_time"),
            default_time_limit=data.get("default_time_limit"),
            default_n_cpu=data.get("default_n_cpu"),
            default_json_db_name=data.get("default_json_db_name"),
            slurm_script_path=data.get("slurm_script_path"),
            antares_versions_on_remote_server=data.get("antares_versions_on_remote_server"),
            max_cores=data.get("max_cores", 64),
            nb_cores=nb_cores,
            enable_nb_core_detection=data.get("enable_nb_cores_detection", False),
        )

    @staticmethod
    def _autodetect_nb_cores() -> object:
        raise NotImplementedError()


@dataclass(frozen=True)
class LauncherConfig:
    """
    Sub config object dedicated to launcher module
    """

    default: str = "local"
    local: Optional[LocalConfig] = LocalConfig()
    slurm: Optional[SlurmConfig] = SlurmConfig()
    batch_size: int = 9999

    @staticmethod
    def from_dict(data: JSON) -> "LauncherConfig":
        local: Optional[LocalConfig] = None
        if "local" in data:
            local = LocalConfig.from_dict(data["local"])

        slurm: Optional[SlurmConfig] = None
        if "slurm" in data:
            slurm = SlurmConfig.from_dict(data["slurm"])

        return LauncherConfig(
            default=data.get("default", "local"),
            local=local,
            slurm=slurm,
            batch_size=data.get("batch_size", 9999),
        )

    @staticmethod
    def get_nb_cores(launcher: str) -> Union[object, Dict[str, int]]:
        """
        This method retrieves the number of cores configuration for a given
        launcher: "local," "slurm," or "default."
        Args:
            launcher: type of launcher local or slurm or default

        Returns: min, max, default of cpu configuration

        """
        info_data = Config.from_yaml_to_dict()
        if launcher == "default":
            launcher = info_data["launcher"]["default"]

        if launcher == "slurm":
            enable_nb_core_detection = info_data["launcher"]["slurm"]["enable_nb_cores_detection"]
            if enable_nb_core_detection:
                return SlurmConfig._autodetect_nb_cores()
            min_cpu = info_data["launcher"]["slurm"]["nb_cores"]["min"]
            max_cpu = info_data["launcher"]["slurm"]["nb_cores"]["max"]
            default = info_data["launcher"]["slurm"]["nb_cores"]["default"]
            return NbCoresConfig.to_json(min_cpu=min_cpu, max_cpu=max_cpu, default=default)
        return LocalConfig._autodetect_nb_cores()


@dataclass(frozen=True)
class LoggingConfig:
    """
    Sub config object dedicated to logging
    """

    logfile: Optional[Path] = None
    json: bool = False
    level: str = "INFO"

    @staticmethod
    def from_dict(data: JSON) -> "LoggingConfig":
        logging_config: Dict[str, Any] = data or {}
        logfile: Optional[str] = logging_config.get("logfile")
        return LoggingConfig(
            logfile=Path(logfile) if logfile is not None else None,
            json=logging_config.get("json", False),
            level=logging_config.get("level", "INFO"),
        )


@dataclass(frozen=True)
class RedisConfig:
    """
    Sub config object dedicated to redis
    """

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None

    @staticmethod
    def from_dict(data: JSON) -> "RedisConfig":
        return RedisConfig(
            host=data["host"],
            port=data["port"],
            password=data.get("password", None),
        )


@dataclass(frozen=True)
class EventBusConfig:
    """
    Sub config object dedicated to eventbus module
    """

    # noinspection PyUnusedLocal
    @staticmethod
    def from_dict(data: JSON) -> "EventBusConfig":
        return EventBusConfig()


@dataclass(frozen=True)
class CacheConfig:
    """
    Sub config object dedicated to cache module
    """

    checker_delay: float = 0.2  # in seconds

    @staticmethod
    def from_dict(data: JSON) -> "CacheConfig":
        return CacheConfig(
            checker_delay=float(data["checker_delay"]) if "checker_delay" in data else 0.2,
        )


@dataclass(frozen=True)
class RemoteWorkerConfig:
    name: str
    queues: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: JSON) -> "RemoteWorkerConfig":
        return RemoteWorkerConfig(name=data["name"], queues=data.get("queues", []))


@dataclass(frozen=True)
class TaskConfig:
    """
    Sub config object dedicated to the task module
    """

    max_workers: int = 5
    remote_workers: List[RemoteWorkerConfig] = field(default_factory=list)

    @staticmethod
    def from_dict(data: JSON) -> "TaskConfig":
        return TaskConfig(
            max_workers=int(data["max_workers"]) if "max_workers" in data else 5,
            remote_workers=list(
                map(
                    lambda x: RemoteWorkerConfig.from_dict(x),
                    data.get("remote_workers", []),
                )
            ),
        )


@dataclass(frozen=True)
class ServerConfig:
    """
    Sub config object dedicated to the server
    """

    worker_threadpool_size: int = 5
    services: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: JSON) -> "ServerConfig":
        return ServerConfig(
            worker_threadpool_size=int(data["worker_threadpool_size"]) if "worker_threadpool_size" in data else 5,
            services=data.get("services", []),
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

    @staticmethod
    def from_dict(data: JSON, res: Optional[Path] = None) -> "Config":
        """
        Parse config from dict.

        Args:
            data: dict struct to parse
            res: resources path is not present in yaml file.

        Returns:

        """
        return Config(
            security=SecurityConfig.from_dict(data.get("security", {})),
            storage=StorageConfig.from_dict(data["storage"]),
            launcher=LauncherConfig.from_dict(data.get("launcher", {})),
            db=DbConfig.from_dict(data["db"]) if "db" in data else DbConfig(),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            debug=data.get("debug", False),
            resources_path=res or Path(),
            root_path=data.get("root_path", ""),
            redis=RedisConfig.from_dict(data["redis"]) if "redis" in data else None,
            eventbus=EventBusConfig.from_dict(data["eventbus"]) if "eventbus" in data else EventBusConfig(),
            cache=CacheConfig.from_dict(data["cache"]) if "cache" in data else CacheConfig(),
            tasks=TaskConfig.from_dict(data["tasks"]) if "tasks" in data else TaskConfig(),
            server=ServerConfig.from_dict(data["server"]) if "server" in data else ServerConfig(),
        )

    @staticmethod
    def from_yaml_file(file: Path, res: Optional[Path] = None) -> "Config":
        """
        Parse config from yaml file.

        Args:
            file: yaml path
            res: resources path is not present in yaml file.

        Returns:

        """
        data = yaml.safe_load(open(file))
        return Config.from_dict(data, res)

    @staticmethod
    def from_yaml_to_dict():
        """Convert yaml file to dictionary"""
        here = Path(__file__).parent.resolve()
        project_path = next(iter(p for p in here.parents if p.joinpath("antarest").exists()))
        file = project_path / "resources/application.yaml"
        data = yaml.safe_load(open(file))
        return data
