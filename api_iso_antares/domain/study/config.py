from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, List

from api_iso_antares.antares_io.reader import IniReader


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
        self.areas = areas or self._parse_areas()

    def next_file(self, name: str) -> "Config":
        copy = deepcopy(self)
        copy.path = copy.path / name
        return copy

    @property
    def area_names(self) -> List[str]:
        return list(self.areas.keys())

    def get_thermals(self, area: str) -> List[str]:
        return self.areas[area].thermals

    def _parse_areas(self) -> Dict[str, Area]:
        areas = (
            (self.root_path / "input/areas/list.txt").read_text().split("\n")
        )
        areas = [a.lower() for a in areas if a != ""]
        return {
            a: Area(
                links=self._parse_links(a), thermals=self._parse_thermal(a)
            )
            for a in areas
        }

    def _parse_thermal(self, area: str) -> List[str]:
        list_ini = IniReader().read(
            self.root_path / f"input/thermal/clusters/{area}/list.ini"
        )
        return list(list_ini.keys())

    def _parse_links(self, area: str) -> List[str]:
        properties_ini = IniReader().read(
            self.root_path / f"input/links/{area}/properties.ini"
        )
        return list(properties_ini.keys())
