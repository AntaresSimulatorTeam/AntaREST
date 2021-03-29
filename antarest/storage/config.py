from dataclasses import dataclass, field
from typing import List, Dict

from dataclasses_json.api import dataclass_json

from antarest.common.config import register_config


@dataclass
class Workspace:
    path: str
    groups: List[str] = field(default_factory=list)


@dataclass_json
@dataclass
class StorageConfig:
    workspaces: Dict[str, Workspace]


get_config = register_config("storage", StorageConfig)
