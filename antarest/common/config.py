import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

import typing
import yaml
from dataclasses_json import DataClassJsonMixin

from antarest.common.custom_types import JSON

config_definitions: typing.Dict[str, typing.Type[DataClassJsonMixin]] = {}
T = typing.TypeVar("T", bound=DataClassJsonMixin)


class Config:
    def __init__(self, data: Optional[JSON] = None):
        self.raw_data = data or dict()
        self.data: typing.Dict[str, Any] = {}
        self._init()

    def __getitem__(self, item: str) -> Any:
        return self._get(item)

    def _init(self):
        global config_definitions
        for k in self.raw_data:
            if k in config_definitions:
                self.data[k] = config_definitions[k].from_dict(
                    self.raw_data[k]
                )
            else:
                self.data[k] = self.raw_data[k]

    def _get(self, key: str) -> Any:
        parts = key.split(".")

        env = "_".join(parts).upper()
        if env in os.environ:
            return os.environ[env]

        data = self.data
        for p in parts:
            if p not in data:
                return None
            data = data[p]
        return deepcopy(data)


class ConfigYaml(Config):
    def __init__(self, file: Path, res: Optional[Path] = None):
        data = yaml.safe_load(open(file))
        data["_internal"] = {}
        data["_internal"]["resources_path"] = res
        Config.__init__(self, data)


def register_config(key: str, class_name: T) -> typing.Callable[[Config], T]:
    global config_definitions
    config_definitions[key] = class_name

    def _get_config(config: Config) -> T:
        return typing.cast(T, config[key])

    return _get_config
