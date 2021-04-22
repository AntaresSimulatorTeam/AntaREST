from pathlib import Path
from typing import Optional, List, Dict

import yaml
from dataclasses import dataclass, field

from antarest.common.custom_types import JSON
from antarest.common.roles import RoleType


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
            default_group_role=RoleType.from_dict(
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

    groups: List[str] = field(default_factory=lambda: [])
    path: Path = Path()

    @staticmethod
    def from_dict(data: JSON) -> "WorkspaceConfig":
        return WorkspaceConfig(
            path=Path(data["path"]), groups=data.get("groups", list())
        )


@dataclass(frozen=True)
class StorageConfig:
    """
    Sub config object dedicated to storage module
    """

    workspaces: Dict[str, WorkspaceConfig] = field(default_factory=lambda: {})
    watcher_lock: bool = True

    @staticmethod
    def from_dict(data: JSON) -> "StorageConfig":
        return StorageConfig(
            workspaces={
                n: WorkspaceConfig.from_dict(w)
                for n, w in data["workspaces"].items()
            },
            watcher_lock=data.get("watcher_lock", True),
        )


@dataclass(frozen=True)
class LocalConfig:
    binaries: Dict[str, Path] = field(default_factory=lambda: {})

    @staticmethod
    def from_dict(data: JSON) -> "LocalConfig":
        return LocalConfig(
            binaries={v: Path(p) for v, p in data["binaries"].items()},
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
    db_primary_key: str = ""
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
            private_key_file=data["private_key_file"],
            key_password=data["key_password"],
            password=data["password"],
            default_wait_time=data["default_wait_time"],
            default_time_limit=data["default_time_limit"],
            default_n_cpu=data["default_n_cpu"],
            default_json_db_name=data["default_json_db_name"],
            slurm_script_path=data["slurm_script_path"],
            db_primary_key=data["db_primary_key"],
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
    local: LocalConfig = LocalConfig()
    slurm: SlurmConfig = SlurmConfig()

    @staticmethod
    def from_dict(data: JSON) -> "LauncherConfig":
        return LauncherConfig(
            default=data.get("default", "local"),
            local=LocalConfig.from_dict(data["local"]),
            slurm=SlurmConfig.from_dict(data["slurm"]),
        )


@dataclass(frozen=True)
class LoggingConfig:
    """
    Sub config object dedicated to logging
    """

    level: str = "INFO"
    path: Optional[Path] = None
    format: Optional[str] = None

    @staticmethod
    def from_dict(data: JSON) -> "LoggingConfig":
        return LoggingConfig(
            level=data["level"],
            path=data.get("path", None),
            format=data.get("format", None),
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

    redis: Optional[RedisConfig] = None

    @staticmethod
    def from_dict(data: JSON) -> "EventBusConfig":
        return EventBusConfig(
            redis=RedisConfig.from_dict(data["redis"])
            if "redis" in data
            else None
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
    logging: LoggingConfig = LoggingConfig()
    debug: bool = True
    resources_path: Path = Path()
    eventbus: EventBusConfig = EventBusConfig()

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
            logging=LoggingConfig.from_dict(data["logging"]),
            debug=data["debug"],
            resources_path=res or Path(),
            eventbus=EventBusConfig.from_dict(data["eventbus"])
            if "eventbus" in data
            else EventBusConfig(),
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
