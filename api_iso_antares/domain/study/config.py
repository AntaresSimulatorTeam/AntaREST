import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, List, Any

from api_iso_antares.antares_io.reader import IniReader


class Area:
    def __init__(self, links: List[str], thermals: List[str]):
        self.links = links
        self.thermals = thermals


class Simulation:
    def __init__(self, name: str, date: str, mode: str):
        self.name = name
        self.date = date
        self.mode = mode

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq"}
        return f"{self.date}{modes[self.mode]}-{self.name}"


class Config:
    def __init__(
        self,
        study_path: Path,
        areas: Optional[Dict[str, Area]] = None,
        outputs: Optional[Dict[int, Simulation]] = None,
    ):
        self.root_path = study_path
        self.path = study_path
        self.areas = areas if areas is not None else self._parse_areas()
        self.outputs = (
            outputs if outputs is not None else self._parse_outputs()
        )

    def next_file(self, name: str) -> "Config":
        copy = deepcopy(self)
        copy.path = copy.path / name
        return copy

    @property
    def area_names(self) -> List[str]:
        return list(self.areas.keys())

    def get_thermals(self, area: str) -> List[str]:
        return self.areas[area].thermals

    def get_links(self, area: str) -> List[str]:
        return self.areas[area].links

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

    def _parse_outputs(self) -> Dict[int, Simulation]:
        files = sorted((self.root_path / "output").iterdir())
        return {
            i: self._parse_output_name(f.name) for i, f in enumerate(files)
        }

    def _parse_output_name(self, name: str) -> Simulation:
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search("^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", name)
        return Simulation(
            date=regex.group(1),
            mode=modes[regex.group(2)],
            name=regex.group(3),
        )
