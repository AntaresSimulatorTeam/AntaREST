import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import Extra

from antarest.core.model import JSON
from antarest.core.utils.utils import DTO
from pydantic.main import BaseModel

from .st_storage import STStorageConfig


class ENR_MODELLING(Enum):
    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"


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

    class Config:
        extra = Extra.forbid

    name: str
    links: Dict[str, Link]
    thermals: List[Cluster]
    renewables: List[Cluster]
    filters_synthesis: List[str]
    filters_year: List[str]
    # since v8.6
    st_storages: List[STStorageConfig] = []


class DistrictSet(BaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    ALL = ["hourly", "daily", "weekly", "monthly", "annual"]
    name: Optional[str] = None
    inverted_set: bool = False
    areas: Optional[List[str]] = None
    output: bool = True
    filters_synthesis: List[str] = ALL
    filters_year: List[str] = ALL

    def get_areas(self, all_areas: List[str]) -> List[str]:
        if self.inverted_set:
            return list(set(all_areas).difference(set(self.areas or [])))
        return self.areas or []


class Simulation(BaseModel):
    """
    Object linked to /output/<simulation_name>/about-the-study/** informations
    """

    name: str
    date: str
    mode: str
    nbyears: int
    synthesis: bool
    by_year: bool
    error: bool
    playlist: Optional[List[int]]
    archived: bool = False
    xpansion: str

    def get_file(self) -> str:
        modes = {"economy": "eco", "adequacy": "adq", "draft": "dft"}
        dash = "-" if self.name else ""
        return f"{self.date}{modes[self.mode]}{dash}{self.name}"


class BindingConstraintDTO(BaseModel):
    id: str
    areas: Set[str]
    clusters: Set[str]


class FileStudyTreeConfig(DTO):
    """
    Root object to handle all study parameters which impact tree structure
    """

    def __init__(
        self,
        study_path: Path,
        path: Path,
        study_id: str,
        version: int,
        output_path: Optional[Path] = None,
        areas: Optional[Dict[str, Area]] = None,
        sets: Optional[Dict[str, DistrictSet]] = None,
        outputs: Optional[Dict[str, Simulation]] = None,
        bindings: Optional[List[BindingConstraintDTO]] = None,
        store_new_set: bool = False,
        archive_input_series: Optional[List[str]] = None,
        enr_modelling: str = ENR_MODELLING.AGGREGATED.value,
        cache: Optional[Dict[str, List[str]]] = None,
        zip_path: Optional[Path] = None,
    ):
        self.study_path = study_path
        self.path = path
        self.study_id = study_id
        self.version = version
        self.output_path = output_path
        self.areas = areas or {}
        self.sets = sets or {}
        self.outputs = outputs or {}
        self.bindings = bindings or []
        self.store_new_set = store_new_set
        self.archive_input_series = archive_input_series or []
        self.enr_modelling = enr_modelling
        self.cache = cache or {}
        self.zip_path = zip_path

    def next_file(
        self, name: str, is_output: bool = False
    ) -> "FileStudyTreeConfig":
        if is_output and name in self.outputs and self.outputs[name].archived:
            zip_path: Optional[Path] = self.path / f"{name}.zip"
        else:
            zip_path = self.zip_path

        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
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
            cache=self.cache,
            zip_path=zip_path,
        )

    def at_file(self, filepath: Path) -> "FileStudyTreeConfig":
        return FileStudyTreeConfig(
            study_path=self.study_path,
            output_path=self.output_path,
            path=filepath,
            study_id=self.study_id,
            version=self.version,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            cache=self.cache,
        )

    def area_names(self) -> List[str]:
        return self.cache.get("%areas", list(self.areas.keys()))

    def set_names(self, only_output: bool = True) -> List[str]:
        return self.cache.get(
            f"%districts%{only_output}",
            [k for k, v in self.sets.items() if v.output or not only_output],
        )

    def get_thermal_names(
        self, area: str, only_enabled: bool = False
    ) -> List[str]:
        return self.cache.get(
            f"%thermal%{area}%{only_enabled}%{area}",
            [
                thermal.id
                for thermal in self.areas[area].thermals
                if not only_enabled or thermal.enabled
            ],
        )

    def get_st_storage_names(self, area: str) -> List[str]:
        return self.cache.get(
            f"%st-storage%{area}", [s.id for s in self.areas[area].st_storages]
        )

    def get_renewable_names(
        self,
        area: str,
        only_enabled: bool = False,
        section_name: bool = True,
    ) -> List[str]:
        return self.cache.get(
            f"%renewable%{area}%{only_enabled}%{section_name}",
            [
                renewable.id if section_name else renewable.name
                for renewable in self.areas[area].renewables
                if not only_enabled or renewable.enabled
            ],
        )

    def get_links(self, area: str) -> List[str]:
        return self.cache.get(
            f"%links%{area}", list(self.areas[area].links.keys())
        )

    def get_filters_synthesis(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_synthesis
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_synthesis
        return self.areas[area].filters_synthesis

    def get_filters_year(
        self, area: str, link: Optional[str] = None
    ) -> List[str]:
        if link:
            return self.areas[area].links[link].filters_year
        if area in self.sets and self.sets[area].output:
            return self.sets[area].filters_year
        return self.areas[area].filters_year


# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str, lower: bool = True) -> str:
    """
    Transform a name into an identifier by replacing consecutive
    invalid characters by a single white space, and then whitespaces
    are striped from both ends.

    Valid characters are `[a-zA-Z0-9_(),& -]` (including space).

    Args:
        name: The name to convert.
        lower: The flag used to turn the identifier in lower case.
    """
    valid_id = _sub_invalid_chars(" ", name).strip()
    return valid_id.lower() if lower else valid_id


class FileStudyTreeConfigDTO(BaseModel):
    study_path: Path
    path: Path
    study_id: str
    version: int
    output_path: Optional[Path] = None
    areas: Dict[str, Area] = dict()
    sets: Dict[str, DistrictSet] = dict()
    outputs: Dict[str, Simulation] = dict()
    bindings: List[BindingConstraintDTO] = list()
    store_new_set: bool = False
    archive_input_series: List[str] = list()
    enr_modelling: str = ENR_MODELLING.AGGREGATED.value
    zip_path: Optional[Path] = None

    @staticmethod
    def from_build_config(
        config: FileStudyTreeConfig,
    ) -> "FileStudyTreeConfigDTO":
        return FileStudyTreeConfigDTO.construct(
            study_path=config.study_path,
            path=config.path,
            study_id=config.study_id,
            version=config.version,
            output_path=config.output_path,
            areas=config.areas,
            sets=config.sets,
            outputs=config.outputs,
            bindings=config.bindings,
            store_new_set=config.store_new_set,
            archive_input_series=config.archive_input_series,
            enr_modelling=config.enr_modelling,
            zip_path=config.zip_path,
        )

    def to_build_config(self) -> FileStudyTreeConfig:
        return FileStudyTreeConfig(
            study_path=self.study_path,
            path=self.path,
            study_id=self.study_id,
            version=self.version,
            output_path=self.output_path,
            areas=self.areas,
            sets=self.sets,
            outputs=self.outputs,
            bindings=self.bindings,
            store_new_set=self.store_new_set,
            archive_input_series=self.archive_input_series,
            enr_modelling=self.enr_modelling,
            zip_path=self.zip_path,
        )
