import abc
from abc import abstractmethod
from typing import List, Tuple, Optional

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


class ICommandExtractor(abc.ABC):
    @abstractmethod
    def extract_area(
        self, study: FileStudy, area_id: str
    ) -> Tuple[List["ICommand"], List["ICommand"]]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: Optional[JSON] = None,
    ) -> List["ICommand"]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def extract_cluster(
        self, study: FileStudy, area_id: str, thermal_id: str
    ) -> List["ICommand"]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def extract_hydro(
        self, study: FileStudy, area_id: str
    ) -> List["ICommand"]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def extract_district(
        self, study: FileStudy, district_id: str
    ) -> List["ICommand"]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: Optional[JSON] = None,
    ) -> List["ICommand"]:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def generate_update_config(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> "ICommand":  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: List[str],
        default_value: Optional[str] = None,
    ) -> "ICommand":  # type: ignore
        raise NotImplementedError()
