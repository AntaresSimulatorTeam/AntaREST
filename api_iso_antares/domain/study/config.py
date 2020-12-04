from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, List


class Area:
    def __init__(self, links: List[str], thermals: List[str]):
        self.links = links
        self.thermals = thermals


class Config:
    def __init__(
        self, study_path: Path, areas: Optional[Dict[str, Area]] = None
    ):
        self.root_path = study_path
        self.path = study_path
        self.areas = areas or dict()

    def next_file(self, name: str) -> "Config":
        copy = deepcopy(self)
        copy.path = copy.path / name
        return copy

    @property
    def area_names(self) -> List[str]:
        return list(self.areas.keys())

    def get_thermals(self, area: str) -> List[str]:
        return self.areas[area].thermals
