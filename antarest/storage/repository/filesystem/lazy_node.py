import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Generic

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import INode, S, G, V


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    Abstract left with implemented a lazy loading for its daughter implementation.
    """

    def __init__(
        self,
        context: ContextServer,
        config: StudyConfig,
    ) -> None:
        self.context = context
        self.config = config

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        self._assert_url_end(url)

        if self.config.path.exists():
            if expanded:
                return self.context.resolver.build_studyfile_uri(
                    self.config.path, self.config.study_id
                )
            else:
                return self.load(url, depth, expanded)
        else:
            data = self.get_link_path().read_text()
            return data if expanded else self.context.resolver.resolve(data)

    def get_link_path(self) -> Path:
        path = self.config.path.parent / (self.config.path.name + ".link")
        return path

    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)

        if isinstance(data, str) and f"studyfile://" in data:
            data = self.context.resolver.resolve(data)
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
