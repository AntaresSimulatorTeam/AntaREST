import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, List, Any

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON


class Link:
    def __init__(self, filters_synthesis: List[str], filters_year: List[str]):
        self.filters_synthesis = filters_synthesis
        self.filters_year = filters_year

    @staticmethod
    def from_fs(properties: JSON) -> "Link":
        return Link(
            filters_year=Link.split(properties["filter-year-by-year"]),
            filters_synthesis=Link.split(properties["filter-synthesis"]),
        )

    @staticmethod
    def split(line: str) -> List[str]:
        return [
            token.strip() for token in line.split(",") if token.strip() != ""
        ]


class Area:
    def __init__(
        self,
        links: Dict[str, Link],
        thermals: List[str],
        filters_synthesis: List[str],
        filters_year: List[str],
    ):
        self.links = links
        self.thermals = thermals
        self.filters_synthesis = filters_synthesis
        self.filters_year = filters_year

    @staticmethod
    def from_fs(root: Path, area: str):
        return Area(
            links=Area._parse_links(root, area),
            thermals=Area._parse_thermal(root, area),
            filters_synthesis=Area._parse_filters_synthesis(root, area),
            filters_year=Area._parse_filters_year(root, area),
        )

    @staticmethod
    def _parse_thermal(root: Path, area: str) -> List[str]:
        list_ini = IniReader().read(
            root / f"input/thermal/clusters/{area}/list.ini"
        )
        return list(list_ini.keys())

    @staticmethod
    def _parse_links(root: Path, area: str) -> Dict[str, Link]:
        properties_ini = IniReader().read(
            root / f"input/links/{area}/properties.ini"
        )
        return {
            link: Link.from_fs(properties_ini[link])
            for link in list(properties_ini.keys())
        }

    @staticmethod
    def _parse_filters_synthesis(root: Path, area: str) -> List[str]:
        filters: str = IniReader().read(
            root / f"input/areas/{area}/optimization.ini"
        )["filtering"]["filter-synthesis"]
        return [f.strip() for f in filters.split(",")]

    @staticmethod
    def _parse_filters_year(root: Path, area: str) -> List[str]:
        filters: str = IniReader().read(
            root / f"input/areas/{area}/optimization.ini"
        )["filtering"]["filter-year-by-year"]
        return Link.split(filters)


class Simulation:
    def __init__(self, name: str, date: str, mode: str, nbyears: int):
        self.name = name
        self.date = date
        self.mode = mode
        self.nbyears = nbyears

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"

    @staticmethod
    def from_fs(path: Path) -> "Simulation":
        modes = {"eco": "economy", "adq": "adequacy"}
        regex: Any = re.search(
            "^([0-9]{8}-[0-9]{4})(eco|adq)-?(.*)", path.name
        )
        return Simulation(
            date=regex.group(1),
            mode=modes[regex.group(2)],
            name=regex.group(3),
            nbyears=Simulation._parse_nbyears(path),
        )

    @staticmethod
    def _parse_nbyears(path: Path) -> int:
        nbyears: int = IniReader().read(
            path / "about-the-study/parameters.ini"
        )["general"]["nbyears"]
        return nbyears


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
        return list(self.areas[area].links.keys())

    def get_filters_synthesis(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_synthesis
        return self.areas[area].filters_synthesis

    def get_filters_year(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_year
        return self.areas[area].filters_year

    def _parse_areas(self) -> Dict[str, Area]:
        areas = (
            (self.root_path / "input/areas/list.txt").read_text().split("\n")
        )
        areas = [a.lower() for a in areas if a != ""]
        return {a: Area.from_fs(self.root_path, a) for a in areas}

    def _parse_outputs(self) -> Dict[int, Simulation]:
        files = sorted((self.root_path / "output").iterdir())
        return {i: Simulation.from_fs(f) for i, f in enumerate(files)}
