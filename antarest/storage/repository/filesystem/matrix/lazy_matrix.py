import os
import shutil
from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Optional, Generic, Tuple, Any

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import INode, S, G, V


class LazyMatrix(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    Abstract left with implemented a lazy loading for its daughter implementation.
    """

    SUFFIX = ".link"

    def __init__(
        self, context: ContextServer, config: StudyConfig, url_prefix: str
    ) -> None:
        self.config = config
        self.url_prefix = url_prefix
        self.context = context

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        self._assert_url(url)
        if self.config.path.suffix == LazyMatrix.SUFFIX:
            if expanded:
                return self.config.path.stem
            else:
                return self.context.matrix.get(self.config.path.stem)
        else:
            data, id = self._matrix_store(depth, expanded, url)
            return id if expanded else data

    def _matrix_store(self, depth, expanded, url) -> Tuple[Any, str]:
        data = self.load(url, depth, expanded)
        id = self.context.matrix.create(data)
        os.remove(self.config.path)
        self.config.path = self.config.path.parent / f"{id}{LazyMatrix.SUFFIX}"
        self.config.path.touch()
        return data, id

    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        self._assert_url(url)

        # if data is pointer
        # get matrix by matrix store

        # if data is dict
        # save in matrix store
        # replace id in file

        return self.dump(data, url)

    @abstractmethod
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        """
        Fetch data on disk.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
