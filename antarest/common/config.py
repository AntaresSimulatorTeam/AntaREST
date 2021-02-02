import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class Config:
    def __init__(self, file: Path):
        self.data = yaml.load(open(file))

    def __getitem__(self, item: str) -> Any:
        return self._get(item)

    def _get(self, key: str) -> Any:
        parts = key.split(".")

        env = "_".join(parts).upper()
        if env in os.environ:
            return os.environ[env]

        data = deepcopy(self.data)
        for p in parts:
            data = data[p]
        return data
