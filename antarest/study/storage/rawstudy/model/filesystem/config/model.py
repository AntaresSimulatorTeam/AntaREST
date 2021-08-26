from pathlib import Path
from typing import Optional, List, Dict

from pydantic.main import BaseModel

from antarest.core.custom_types import JSON


class Cluster(BaseModel):
    """
    Object linked to /input/thermal/clusters/<area>/list.ini
    """

    id: str
    name: str
    enabled: bool = True


class Link(BaseModel):
    """
    Object linked to /input/links/<link>/properties.ini information
    """

    filters_synthesis: List[str]
    filters_year: List[str]

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


class Area(BaseModel):
    """
    Object linked to /input/<area>/optimization.ini information
    """

    links: Dict[str, Link]
    thermals: List[Cluster]
    renewables: List[Cluster]
    filters_synthesis: List[str]
    filters_year: List[str]


class Set(BaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL = ["hourly", "daily", "weekly", "monthly", "annual"]
    areas: Optional[List[str]] = None
    filters_synthesis: List[str] = ALL
    filters_year: List[str] = ALL


class Simulation(BaseModel):
    """
    Object linked to /output/<simulation>/about-the-study/** informations
    """

    name: str
    date: str
    mode: str
    nbyears: int
    synthesis: bool
    by_year: bool
    error: bool

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq", "draft": "dft"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"


class FileStudyTreeConfig(BaseModel):
    """
    Root object to handle all study parameters which impact tree structure
    """

    study_path: Path
    path: Path
    study_id: str
    version: int
    areas: Dict[str, Area] = dict()
    sets: Dict[str, Set] = dict()
    outputs: Dict[str, Simulation] = dict()
    bindings: List[str] = list()
    store_new_set: bool = False
    archive_input_series: List[str] = list()
    enr_modelling: str = "aggregated"

    def next_file(self, name: str) -> "FileStudyTreeConfig":
        return FileStudyTreeConfig(
            study_path=self.study_path,
            path=self.path / name,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
        )

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

    def get_renewable_names(
        self,
        area: str,
        only_enabled: bool = False,
        section_name: bool = True,
    ) -> List[str]:
        return [
            renewable.id if section_name else renewable.name
            for renewable in self.areas[area].renewables
            if not only_enabled or renewable.enabled
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
