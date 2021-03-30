import logging
from dataclasses import dataclass
from typing import Optional

from dataclasses_json.api import dataclass_json

from antarest.common.config import Config, register_config


@dataclass_json
@dataclass
class LoggingConfig:
    path: Optional[str] = None
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


get_config = register_config("logging", LoggingConfig)


def configure_logger(config: Config) -> None:
    logging_config = get_config(config) or LoggingConfig()
    logging.basicConfig(
        filename=logging_config.path,
        format=logging_config.format,
        level=logging_config.level,
    )
