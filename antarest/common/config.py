import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, List, Dict

import yaml
from dataclasses import dataclass, field

from antarest.common.custom_types import JSON


@dataclass(frozen=True)
class SecurityConfig:
    jwt_key: str = ""
    admin_pwd: str = ""
    disable: bool = False

    @staticmethod
    def from_dict(data: JSON) -> "SecurityConfig":
        return SecurityConfig(
            jwt_key=data["jwt"]["key"],
            admin_pwd=data["login"]["admin"]["pwd"],
            disable=data.get("disable", False),
        )


@dataclass(frozen=True)
class WorkspaceConfig:
    groups: List[str] = field(default_factory=lambda: [])
    path: Path = Path()

    @staticmethod
    def from_dict(data: JSON) -> "WorkspaceConfig":
        return WorkspaceConfig(
            path=Path(data["path"]), groups=data.get("groups", list())
        )


@dataclass(frozen=True)
class StorageConfig:
    workspaces: Dict[str, WorkspaceConfig] = field(default_factory=lambda: {})

    @staticmethod
    def from_dict(data: JSON) -> "StorageConfig":
        return StorageConfig(
            workspaces={
                n: WorkspaceConfig.from_dict(w)
                for n, w in data["workspaces"].items()
            }
        )


@dataclass(frozen=True)
class LauncherConfig:
    binaries: Dict[str, Path] = field(default_factory=lambda: {})
    default: str = "local"

    @staticmethod
    def from_dict(data: JSON) -> "LauncherConfig":
        return LauncherConfig(
            binaries={
                v: Path(p) for v, p in data["local"]["binaries"].items()
            },
            default=data.get("default", "local"),
        )


@dataclass(frozen=True)
class LoggingConfig:
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
    host: str = ""
    port: int = 0

    @staticmethod
    def from_dict(data: JSON) -> "RedisConfig":
        return RedisConfig(host=data["host"], port=data["port"])


@dataclass(frozen=True)
class EventBusConfig:
    redis: RedisConfig = RedisConfig()

    @staticmethod
    def from_dict(data: JSON) -> "EventBusConfig":
        return EventBusConfig(
            redis=RedisConfig.from_dict(data["redis"])
            if "redis" in data
            else RedisConfig()
        )


@dataclass(frozen=True)
class Config:
    security: SecurityConfig = SecurityConfig()
    storage: StorageConfig = StorageConfig()
    launcher: LauncherConfig = LauncherConfig()
    db_url: str = ""
    logging: LoggingConfig = LoggingConfig()
    debug: bool = True
    resources_path: Optional[Path] = None
    eventbus: EventBusConfig = EventBusConfig()

    @staticmethod
    def from_dict(data: JSON, res: Optional[Path] = None) -> "Config":
        return Config(
            security=SecurityConfig.from_dict(data["security"]),
            storage=StorageConfig.from_dict(data["storage"]),
            launcher=LauncherConfig.from_dict(data["launcher"]),
            db_url=data["db"]["url"],
            logging=LoggingConfig.from_dict(data["logging"]),
            debug=data["debug"],
            resources_path=res,
            eventbus=EventBusConfig.from_dict(data["eventbus"])
            if "eventbus" in data
            else EventBusConfig(),
        )

    @staticmethod
    def from_yaml_file(file: Path, res: Optional[Path] = None) -> "Config":
        data = yaml.safe_load(open(file))
        return Config.from_dict(data, res)
