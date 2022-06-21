from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Dict, TypeVar, Generic, Any, Tuple
from zipfile import ZipFile

from antarest.core.exceptions import ShouldNotHappenException
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


class INode(ABC, Generic[G, S, V]):
    """
    Abstract tree element, have to be implemented to create hub or left.
    """

    def __init__(self, config: FileStudyTreeConfig):
        self.config = config

    @abstractmethod
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> G:
        """
        Ask data inside tree.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion
            formatted: ask for raw file transformation (for matrix)

        Returns: json

        """
        raise NotImplementedError()

    @abstractmethod
    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> "INode[G,S,V]":
        """
        Ask data inside tree.

        Args:
            url: data path to retrieve

        Returns: json

        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, url: Optional[List[str]] = None) -> None:
        """
        Delete a node located at some url

        Args:
            url: data path to delete
        """

    @abstractmethod
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Save data inside tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def check_errors(
        self, data: V, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        """
        List inconsistency error between data and study configuration.
        Args:
            data: data to compare
            url: data path to compare
            raising: raise error if inconsistency occurs

        Returns: list of errors belongs to this node or children

        """
        raise NotImplementedError()

    @abstractmethod
    def normalize(self) -> None:
        """
        Scan tree to send matrix in matrix store and replace by its links
        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def denormalize(self) -> None:
        """
        Scan tree to fetch matrix by its links
        Returns:

        """
        raise NotImplementedError()

    def _assert_url_end(self, url: Optional[List[str]] = None) -> None:
        """
        Raise error if elements remain in url
        Args:
            url: data path

        Returns:

        """
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )

    def _extract_file_to_tmp_dir(
        self,
    ) -> Tuple[Path, Any]:
        """
        Happens when the file is inside an archive (aka self.config.zip_file is set)
        Unzip the file into a temporary directory.

        Returns:
            The actual path of the extracted file
            the tmp_dir object which MUST be cleared after use of the file
        """
        if self.config.zip_path is None:
            raise ShouldNotHappenException()
        zip_path_without_extension = str(self.config.zip_path).split(".")[0]
        inside_zip_path = (
            self.config.zip_path.stem
            + "/"
            + str(self.config.path)[len(zip_path_without_extension) + 1 :]
        )
        tmp_dir = TemporaryDirectory()
        if self.config.zip_path:
            with ZipFile(self.config.zip_path) as zip_obj:
                zip_obj.extract(inside_zip_path, tmp_dir.name)
            path = Path(tmp_dir.name) / inside_zip_path
            return path, tmp_dir
        else:
            raise ShouldNotHappenException()


TREE = Dict[str, INode[Any, Any, Any]]
