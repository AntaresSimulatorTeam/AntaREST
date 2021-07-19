from pathlib import Path
from typing import Optional, List, Dict

from antarest.core.custom_types import JSON
from antarest.core.persistence import DTO


class ThermalCluster(DTO):
    """
    Object linked to /input/thermal/clusters/<area>/list.ini
    """

    def __init__(self, id: str, enabled: bool = True):
        self.id = id
        self.enabled = enabled


class Link(DTO):
    """
    Object linked to /input/links/<link>/properties.ini information
    """

    def __init__(self, filters_synthesis: List[str], filters_year: List[str]):
        self.filters_synthesis = filters_synthesis
        self.filters_year = filters_year

    @staticmethod
    def from_json(properties: JSON) -> "Link":
        return Link(
            filters_year=Link.split(properties["filter-year-by-year"]),
            filters_synthesis=Link.split(properties["filter-synthesis"]),
        )

    @staticmethod
    def split(line: str) -> List[str]:
        return [
            token.strip() for token in line.split(",") if token.strip() != ""
        ]


class Area(DTO):
    """
    Object linked to /input/<area>/optimization.ini information
    """

    def __init__(
        self,
        links: Dict[str, Link],
        thermals: List[ThermalCluster],
        filters_synthesis: List[str],
        filters_year: List[str],
    ):
        self.links = links
        self.thermals = thermals
        self.filters_synthesis = filters_synthesis
        self.filters_year = filters_year


class Set(DTO):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL = ["hourly", "daily", "weekly", "monthly", "annual"]

    def __init__(
        self,
        areas: Optional[List[str]] = None,
        filters_synthesis: List[str] = ALL,
        filters_year: List[str] = ALL,
    ):
        self.areas = areas
        self.filters_synthesis = filters_synthesis
        self.filters_year = filters_year


class Simulation(DTO):
    """
    Object linked to /output/<simulation>/about-the-study/** informations
    """

    def __init__(
        self,
        name: str,
        date: str,
        mode: str,
        nbyears: int,
        synthesis: bool,
        by_year: bool,
        error: bool,
    ):
        self.name = name
        self.date = date
        self.mode = mode
        self.nbyears = nbyears
        self.synthesis = synthesis
        self.by_year = by_year
        self.error = error

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq", "draft": "dft"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"


class StudyConfig(DTO):
    """
    Root object to handle all study parameters which impact tree structure
    """

    def __init__(
        self,
        study_path: Path,
        study_id: str,
        areas: Optional[Dict[str, Area]] = None,
        sets: Optional[Dict[str, Set]] = None,
        outputs: Optional[Dict[str, Simulation]] = None,
        bindings: Optional[List[str]] = None,
        store_new_set: bool = False,
    ):
        self.root_path = study_path
        self.path = study_path
        self.areas = areas or dict()
        self.sets = sets or dict()
        self.outputs = outputs or dict()
        self.bindings = bindings or list()
        self.store_new_set = store_new_set
        self.study_id = study_id

    def next_file(self, name: str) -> "StudyConfig":
        copy = StudyConfig(
            self.root_path,
            self.study_id,
            self.areas,
            self.sets,
            self.outputs,
            self.bindings,
            self.store_new_set,
        )
        copy.path = self.path / name
        return copy

    def area_names(self) -> List[str]:
        return list(self.areas.keys())

    def set_names(self) -> List[str]:
        return list(self.sets.keys())

    def get_thermal_names(
        self, area: str, only_enabled: bool = False
    ) -> List[str]:
        return [
            thermal.id
            for thermal in self.areas[area].thermals
            if not only_enabled or thermal.enabled
        ]

    def get_links(self, area: str) -> List[str]:
        return list(self.areas[area].links.keys())

    def get_filters_synthesis(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_synthesis
        if area in self.sets:
            return self.sets[area].filters_synthesis
        return self.areas[area].filters_synthesis

    def get_filters_year(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_year
        if area in self.sets:
            return self.sets[area].filters_year
        return self.areas[area].filters_year


def transform_name_to_id(name: str) -> str:
    """This transformation was taken from the cpp Antares Simulator.."""
    duppl = False
    study_id = ""
    for c in name:
        if (
            (c >= "a" and c <= "z")
            or (c >= "A" and c <= "Z")
            or (c >= "0" and c <= "9")
            or c == "_"
            or c == "-"
            or c == "("
            or c == ")"
            or c == ","
            or c == "&"
            or c == " "
        ):
            study_id += c
            duppl = False
        else:
            if not duppl:
                study_id += " "
                duppl = True

    return study_id.strip().lower()
