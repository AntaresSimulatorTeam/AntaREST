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
        url_prefix: str,
    ) -> None:
        self.context = context
        self.config = config
        self.url_prefix = url_prefix

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        self._assert_url_end(url)
        if expanded:
            if self.config.path.exists():
                return self.context.resolver.build_studyfile_uri(
                    self.config.path, self.config.study_id
                )
            else:
                path = self._get_link_path()
                return path.read_text()
        else:
            if self.config.path.exists():
                return self.load(url, depth, expanded)
            else:
                path = self._get_link_path()
                return self.context.resolver.resolve(path.read_text())

    def get_link_path(self):
        path = self.config.path.parent / (self.config.path.name + ".link")
        return path

    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)

        if isinstance(data, str) and f"studyfile://" in data:
            src = self.context.resolver.resolve(data)
            if src != self.config.path:
                self.config.path.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(src, self.config.path)
            return None

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
