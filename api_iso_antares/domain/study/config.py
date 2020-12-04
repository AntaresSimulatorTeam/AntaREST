from copy import deepcopy
from pathlib import Path


class Config:
    def __init__(self, study_path: Path):
        self.root_path = study_path
        self.path = study_path

    def next_file(self, name: str) -> "Config":
        copy = deepcopy(self)
        copy.path = copy.path / name
        return copy
