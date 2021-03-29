from dataclasses import dataclass
from typing import Optional

from dataclasses_json.api import dataclass_json

from antarest.common.config import register_config


@dataclass
class RedisConfig:
    host: str
    port: int = 6379


@dataclass_json
@dataclass
class EventBusConfig:
    redis: Optional[RedisConfig] = None


get_config = register_config("eventbus", EventBusConfig)
