import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml

from antarest.core.custom_types import JSON
from antarest.core.roles import RoleType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExternalAuthConfig:
    """
    Sub config object dedicated to external auth service
    """

    url: Optional[str] = None
    default_group_role: RoleType = RoleType.READER

    @staticmethod
    def from_dict(data: JSON) -> "ExternalAuthConfig":
        return ExternalAuthConfig(
            url=data.get("url", None),
            default_group_role=RoleType(
                data.get("default_group_role", RoleType.READER.value)
            ),
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
            jwt_key=data["jwt"]["key"],
            admin_pwd=data["login"]["admin"]["pwd"],
            disabled=data.get("disabled", False),
            external_auth=ExternalAuthConfig.from_dict(
                data.get("external_auth", {})
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

    @staticmethod
    def from_dict(data: JSON) -> "WorkspaceConfig":
        return WorkspaceConfig(
            path=Path(data["path"]),
            groups=data.get("groups", list()),
            filter_in=data.get("filter_in", [".*"]),
            filter_out=data.get("filter_out", list()),
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
    watcher_lock: bool = True
    watcher_lock_delay: int = 10

    @staticmethod
    def from_dict(data: JSON) -> "StorageConfig":
        return StorageConfig(
            tmp_dir=Path(data.get("tmp_dir", tempfile.gettempdir())),
            matrixstore=Path(data["matrixstore"]),
            workspaces={
                n: WorkspaceConfig.from_dict(w)
                for n, w in data["workspaces"].items()
            },
            archive_dir=Path(data["archive_dir"]),
            watcher_lock=data.get("watcher_lock", True),
            watcher_lock_delay=data.get("watcher_lock_delay", 10),
        )


@dataclass(frozen=True)
class LocalConfig:
    binaries: Dict[str, Path] = field(default_factory=lambda: {})

    @staticmethod
    def from_dict(data: JSON) -> Optional["LocalConfig"]:
        return LocalConfig(
            binaries={str(v): Path(p) for v, p in data["binaries"].items()},
        )


@dataclass(frozen=True)
class SlurmConfig:
    local_workspace: Path = Path()
    username: str = ""
    hostname: str = ""
    port: int = 0
    private_key_file: Path = Path()
    key_password: str = ""
    password: str = ""
    default_wait_time: int = 0
    default_time_limit: int = 0
    default_n_cpu: int = 0
    default_json_db_name: str = ""
    slurm_script_path: str = ""
    antares_versions_on_remote_server: List[str] = field(
        default_factory=lambda: []
    )

    @staticmethod
    def from_dict(data: JSON) -> "SlurmConfig":
        return SlurmConfig(
            local_workspace=Path(data["local_workspace"]),
            username=data["username"],
            hostname=data["hostname"],
            port=data["port"],
            private_key_file=data.get("private_key_file", None),
            key_password=data.get("key_password", None),
            password=data.get("password", None),
            default_wait_time=data["default_wait_time"],
            default_time_limit=data["default_time_limit"],
            default_n_cpu=data["default_n_cpu"],
            default_json_db_name=data["default_json_db_name"],
            slurm_script_path=data["slurm_script_path"],
            antares_versions_on_remote_server=data[
                "antares_versions_on_remote_server"
            ],
        )


@dataclass(frozen=True)
class LauncherConfig:
    """
    Sub config object dedicated to launcher module
    """

    default: str = "local"
    local: Optional[LocalConfig] = LocalConfig()
    slurm: Optional[SlurmConfig] = SlurmConfig()

    @staticmethod
    def from_dict(data: JSON) -> "LauncherConfig":
        try:
            local = LocalConfig.from_dict(data["local"])
        except KeyError as e:
            logger.error("Could not load local launcher", exc_info=e)
            local = None

        slurm: Optional[SlurmConfig]
        try:
            slurm = SlurmConfig.from_dict(data["slurm"])
        except KeyError as e:
            logger.error("Could not load slurm launcher", exc_info=e)
            slurm = None
        return LauncherConfig(
            default=data.get("default", "local"),
            local=local,
            slurm=slurm,
        )


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
        logfile: Optional[str] = logging_config.get("logfile", None)
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

    @staticmethod
    def from_dict(data: JSON) -> "RedisConfig":
        return RedisConfig(host=data["host"], port=data["port"])


@dataclass(frozen=True)
class EventBusConfig:
    """
    Sub config object dedicated to eventbus module
    """

    @staticmethod
    def from_dict(data: JSON) -> "EventBusConfig":
        return EventBusConfig()


@dataclass(frozen=True)
class CacheConfig:
    """
    Sub config object dedicated to cache module
    """

    checker_delay: float = 0.2  # in ms

    @staticmethod
    def from_dict(data: JSON) -> "CacheConfig":
        return CacheConfig(
            checker_delay=float(data["checker_delay"])
            if "checker_delay" in data
            else 0.2,
        )


@dataclass(frozen=True)
class TaskConfig:
    """
    Sub config object dedicated to the task module
    """

    max_workers: int = 5

    @staticmethod
    def from_dict(data: JSON) -> "TaskConfig":
        return TaskConfig(
            max_workers=int(data["max_workers"])
            if "max_workers" in data
            else 5
        )


@dataclass(frozen=True)
class Config:
    """
    Root server config
    """

    security: SecurityConfig = SecurityConfig()
    storage: StorageConfig = StorageConfig()
    launcher: LauncherConfig = LauncherConfig()
    db_url: str = ""
    db_admin_url: Optional[str] = None
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
            security=SecurityConfig.from_dict(data["security"]),
            storage=StorageConfig.from_dict(data["storage"]),
            launcher=LauncherConfig.from_dict(data["launcher"]),
            db_url=data["db"]["url"],
            db_admin_url=data["db"].get("admin_url", None),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            debug=data["debug"],
            resources_path=res or Path(),
            root_path=data.get("root_path", ""),
            redis=RedisConfig.from_dict(data["redis"])
            if "redis" in data
            else None,
            eventbus=EventBusConfig.from_dict(data["eventbus"])
            if "eventbus" in data
            else EventBusConfig(),
            cache=CacheConfig.from_dict(data["cache"])
            if "cache" in data
            else CacheConfig(),
            tasks=TaskConfig.from_dict(data["tasks"])
            if "tasks" in data
            else TaskConfig(),
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
