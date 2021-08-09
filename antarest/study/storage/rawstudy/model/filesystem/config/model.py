from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic.main import BaseModel

from antarest.core.custom_types import JSON
from distutils.util import strtobool


class Cluster(BaseModel):
    """
    Object linked to /input/thermal/clusters/<area>/list.ini
    """
    id: str
    enabled: bool = True
    name: Optional[str] = None

    @staticmethod
    def from_json(data: JSON) -> "Cluster":
        return Cluster(
            id=data["id"],
            enabled=data["enabled"],
            name=data["name"] if "name" in data.keys() else data["id"]
        )


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

    @staticmethod
    def from_json(data: JSON) -> "Area":
        links = data["links"]
        for link in links.keys():
            tmp_elm = Link.from_json(link)
            links[link] = tmp_elm

        thermals = data["thermals"]
        for index, thermal in enumerate(thermals):
            tmp_elm = Cluster.from_json(thermal)
            thermals[index] = tmp_elm

        renewables = data["renewables"]
        for index, renewable in enumerate(renewables):
            tmp_elm = Cluster.from_json(renewable)
            renewables[index] = tmp_elm

        return Area(
            links=links,
            thermals=thermals,
            renewables=renewables,
            filters_synthesis=data["filters_synthesis"],
            filters_year=data["filters_year"],
        )


class Set(BaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL = ["hourly", "daily", "weekly", "monthly", "annual"]
    areas: Optional[List[str]] = None
    filters_synthesis: List[str] = ALL
    filters_year: List[str] = ALL

    @staticmethod
    def from_json(data: JSON) -> "Set":
        return Set(
            areas=data["areas"] if "areas" in data.keys() else None,
            filters_synthesis=data["filters_synthesis"],
            filters_year=data["filters_year"],
        )


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

    @staticmethod
    def from_json(data: JSON) -> "Simulation":
        return Simulation(
            name=data["name"],
            date=data["date"],
            mode=data["mode"],
            nbyears=int(data["nbyears"]),
            synthesis=data["synthesis"],
            by_year=data["by_year"],
            error=data["error"],
        )

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
    areas: Optional[Dict[str, Area]] = None
    sets: Optional[Dict[str, Set]] = None
    outputs: Optional[Dict[str, Simulation]] = None
    bindings: Optional[List[str]] = None
    store_new_set: bool = False
    archive_input_series: Optional[List[str]] = None
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

    @staticmethod
    def from_json(data: JSON) -> "FileStudyTreeConfig":
        areas = data["areas"] if "areas" in data.keys() else None
        if areas is not None:
            for area in areas.keys():
                tmp_elm = Area.from_json(areas[area])
                areas[area] = tmp_elm

        sets = data["sets"] if "sets" in data.keys() else None
        if sets is not None:
            for set_elm in sets.keys():
                tmp_elm = Set.from_json(sets[set_elm])
                sets[set_elm] = tmp_elm

        outputs = data["outputs"] if "outputs" in data.keys() else None
        if outputs is not None:
            for output in outputs.keys():
                tmp_elm = Simulation.from_json(outputs[output])
                outputs[output] = tmp_elm

        return FileStudyTreeConfig(
            study_path=Path(data["study_path"]),
            path=Path(data["path"]),
            study_id=data["study_id"],
            version=int(data["version"]),
            areas=areas,
            sets=sets,
            outputs=outputs,
            bindings=data["bindings"] if "bindings" in data.keys() else None,
            store_new_set=data["store_new_set"]
            if "store_new_set" in data.keys()
            else False,
            archive_input_series=data["archive_input_series"]
            if "archive_input_series" in data.keys()
            else None,
            enr_modelling=data["aggregated"],
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
